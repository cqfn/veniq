public class ThrowInline
{
    private ListenableFuture<PrestoThriftPageResult> extracted()
    {
        Iterator<ListenableFuture<PrestoThriftPageResult>> iterator = dataRequests.iterator();
        while (iterator.hasNext()) {
            ListenableFuture<PrestoThriftPageResult> future = iterator.next();
            if (future.isDone()) {
                iterator.remove();
                return future;
            }
        }
        throw new IllegalStateException("No completed splits in the queue");
    }
	
	public Page target()
    {
        if (finished) {
            return null;
        }
        if (!loadAllSplits()) {
            return null;
        }
        if (dataSignalFuture == null) {
            checkState(contexts.isEmpty() && dataRequests.isEmpty(), "some splits are already started");
            if (splits.isEmpty()) {
                finished = true;
                return null;
            }
            for (int i = 0; i < min(lookupRequestsConcurrency, splits.size()); i++) {
                startDataFetchForNextSplit();
            }
            updateSignalAndStatusFutures();
        }
        if (!dataSignalFuture.isDone()) {
            return null;
        }
        ListenableFuture<PrestoThriftPageResult> resultFuture = extracted();
        RunningSplitContext resultContext = contexts.remove(resultFuture);
        checkState(resultContext != null, "no associated context for the request");
        PrestoThriftPageResult pageResult = getFutureValue(resultFuture);
        Page page = pageResult.toPage(outputColumnTypes);
        if (page != null) {
            long pageSize = page.getSizeInBytes();
            completedBytes += pageSize;
            completedPositions += page.getPositionCount();
            stats.addIndexPageSize(pageSize);
        }
        else {
            stats.addIndexPageSize(0);
        }
        if (pageResult.getNextToken() != null) {
            sendDataRequest(resultContext, pageResult.getNextToken());
            updateSignalAndStatusFutures();
            return page;
        }
        if (splitIndex < splits.size()) {
            startDataFetchForNextSplit();
            updateSignalAndStatusFutures();
        }
        else if (!dataRequests.isEmpty()) {
            updateSignalAndStatusFutures();
        }
        else {
            dataSignalFuture = null;
            statusFuture = null;
            finished = true;
        }
        return page;
    }
}