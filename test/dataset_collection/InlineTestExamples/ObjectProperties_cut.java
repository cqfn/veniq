
public class ObjectPropertiesEditor extends AbstractDatabaseObjectEditor<DBSObject> implements IEntityStructureEditor,
IRefreshablePart,
IProgressControlProvider,
ITabbedFolderContainer,
ISearchContextProvider,
INavigatorModelView,
IEntityEditorContext,
IDatabasePostSaveProcessor
{
private void createPropertyBrowser(Composite container)
{
pageControl.setRedraw(false);
try {
	TabbedFolderInfo[] folders = collectFolders(this);
	if (folders.length == 0) {
		createPropertiesPanel(container);
	} else {
		Composite foldersParent = container;
		if (hasPropertiesEditor() && DBWorkbench.getPlatform().getPreferenceStore().getBoolean(NavigatorPreferences.ENTITY_EDITOR_DETACH_INFO)) {
			sashForm = UIUtils.createPartDivider(getSite().getPart(), container, SWT.VERTICAL);
			sashForm.setLayoutData(new GridData(GridData.FILL_BOTH));
			foldersParent = sashForm;

			createPropertiesPanel(sashForm);
		}
		createFoldersPanel(foldersParent, folders);
	}

	// Create props
	if (DBWorkbench.getPlatform().getPreferenceStore().getBoolean(NavigatorPreferences.ENTITY_EDITOR_DETACH_INFO)) {
		if (hasPropertiesEditor()) {
			propertiesPanel = new TabbedFolderPageForm(this, pageControl, getEditorInput());

			propertiesPanel.createControl(propsPlaceholder);
		}
	}

	if (sashForm != null) {
		//Runnable sashUpdater = this::updateSashWidths;
		//sashUpdater.run();
		//UIUtils.asyncExec(sashUpdater);
		if (sashForm.isDisposed()) {
			return;
		}
		 
		//		if (propsPlaceholder != null) {
			Point propsSize = propsPlaceholder.computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
			Point sashSize = sashForm.getParent().getSize();
			if (sashSize.x <= 0 || sashSize.y <= 0) {
				// This may happen if EntityEditor created with some other active editor (i.e. props editor not visible)
				propsSize.y += 10;
				sashSize = getParentSize(sashForm);
				//sashSize.y += 20;
			}
			if (sashSize.x > 0 && sashSize.y > 0) {
				float ratio = (float) propsSize.y / (float) sashSize.y;
				int propsRatio = Math.min(1000, (int) (1000 * ratio));
				int[] newWeights = {propsRatio, 1000 - propsRatio};
				if (!Arrays.equals(newWeights, sashForm.getWeights())) {
					sashForm.setWeights(newWeights);
					//sashForm.layout();
				}
			}
		 
		/*
		} else {
			String sashStateStr = DBWorkbench.getPlatform().getPreferenceStore().getString(NavigatorPreferences.ENTITY_EDITOR_INFO_SASH_STATE);
			int sashPanelHeight = !CommonUtils.isEmpty(sashStateStr) ? Integer.parseInt(sashStateStr) : 400;
			if (sashPanelHeight < 0) sashPanelHeight = 0;
			if (sashPanelHeight > 1000) sashPanelHeight = 1000;
		 
			sashForm.setWeights(new int[] { sashPanelHeight, 1000 - sashPanelHeight });
			//sashForm.layout();
		 
			sashForm.getChildren()[0].addListener(SWT.Resize, event -> {
				if (sashForm != null) {
					int[] weights = sashForm.getWeights();
					if (weights != null && weights.length > 0) {
						int topWeight = weights[0];
						if (topWeight == 0) topWeight = 1;
						DBWorkbench.getPlatform().getPreferenceStore().setValue(NavigatorPreferences.ENTITY_EDITOR_INFO_SASH_STATE, topWeight);
					}
				}
			});
		}
		*/
	}
	pageControl.layout(true, true);
} finally {
	pageControl.setRedraw(true);
}
}

private void updateSashWidths() {
if (sashForm.isDisposed()) {
	return;
}

//        if (propsPlaceholder != null) {
	Point propsSize = propsPlaceholder.computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
	Point sashSize = sashForm.getParent().getSize();
	if (sashSize.x <= 0 || sashSize.y <= 0) {
		// This may happen if EntityEditor created with some other active editor (i.e. props editor not visible)
		propsSize.y += 10;
		sashSize = getParentSize(sashForm);
		//sashSize.y += 20;
	}
	if (sashSize.x > 0 && sashSize.y > 0) {
		float ratio = (float) propsSize.y / (float) sashSize.y;
		int propsRatio = Math.min(1000, (int) (1000 * ratio));
		int[] newWeights = {propsRatio, 1000 - propsRatio};
		if (!Arrays.equals(newWeights, sashForm.getWeights())) {
			sashForm.setWeights(newWeights);
			//sashForm.layout();
		}
	}

/*
} else {
	String sashStateStr = DBWorkbench.getPlatform().getPreferenceStore().getString(NavigatorPreferences.ENTITY_EDITOR_INFO_SASH_STATE);
	int sashPanelHeight = !CommonUtils.isEmpty(sashStateStr) ? Integer.parseInt(sashStateStr) : 400;
	if (sashPanelHeight < 0) sashPanelHeight = 0;
	if (sashPanelHeight > 1000) sashPanelHeight = 1000;

	sashForm.setWeights(new int[] { sashPanelHeight, 1000 - sashPanelHeight });
	//sashForm.layout();

	sashForm.getChildren()[0].addListener(SWT.Resize, event -> {
		if (sashForm != null) {
			int[] weights = sashForm.getWeights();
			if (weights != null && weights.length > 0) {
				int topWeight = weights[0];
				if (topWeight == 0) topWeight = 1;
				DBWorkbench.getPlatform().getPreferenceStore().setValue(NavigatorPreferences.ENTITY_EDITOR_INFO_SASH_STATE, topWeight);
			}
		}
	});
}
*/
}

}