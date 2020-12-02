class Test {
    void activatePart()
    {
        createResultSetView();
        if (!loaded && !isSuspendDataQuery()) {
            if (isReadyToRun()) {
                resultSetView.setStatus(getDataQueryMessage());
                DBDDataFilter dataFilter = getEditorDataFilter();
                if (dataFilter == null) {
                    resultSetView.refresh();
                } else {
                    resultSetView.refreshWithFilter(dataFilter);
                }
                loaded = true;
            }
        }
    }
}