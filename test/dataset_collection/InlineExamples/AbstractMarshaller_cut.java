public abstract class AbstractMarshaller implements Marshaller, Unmarshaller {
	
    public synchronized void removeChild(String propertyName, C component) {
        verifyWrite();
        if (component == null) {
            throw new IllegalArgumentException("component == null"); //NOI18N
        }
        if (! _getChildren().contains(component)) {
            throw new IllegalArgumentException(
                    "component to be deleted is not a child"); //NOI18N
        }
        _removeChildQuietly(component, _getChildren());
        firePropertyChange(propertyName, component, null);
        fireChildRemoved();
    }

		protected void fireChildRemoved() {
			getModel().fireComponentChangedEvent(new ComponentEvent(this,
					ComponentEvent.EventType.CHILD_REMOVED));
		}
	
}