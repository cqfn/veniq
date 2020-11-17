public class UninstallStep implements WizardDescriptor.FinishablePanel<WizardDescriptor> {
    private void doAction () {
        // proceed operation
        Restarter r;
        try {
            if ((r = handleAction ()) != null) {
                presentActionNeedsRestart (r);
            } else {
                presentActionDone ();
            }
        } catch (OperationException ex) {
            presentActionFailed (ex);
        }
        fireChange ();
    }

    private Restarter handleAction () throws OperationException {
        assert model.getBaseContainer () != null : "getBaseContainers() returns not null container.";
        support = (OperationSupport) model.getBaseContainer ().getSupport ();
        assert support != null : "OperationSupport cannot be null because OperationContainer " +
                "contains elements: " + model.getBaseContainer ().listAll () + " and invalid elements " + model.getBaseContainer ().listInvalid ();
        if (support == null) {
            err.log(Level.WARNING, "OperationSupport cannot be null because OperationContainer contains elements: "
                    + "{0} and invalid elements {1}", new Object[]{model.getBaseContainer().listAll(), model.getBaseContainer().listInvalid()});
            if (!model.getBaseContainer().listInvalid().isEmpty()) {
                // cannot continue if there are invalid elements
                throw new OperationException(OperationException.ERROR_TYPE.UNINSTALL,
                        UninstallStep_NullSupport_InvalidElements(model.getBaseContainer().listInvalid()));
            } else if (model.getBaseContainer().listAll().isEmpty()) {
                // it's weird, there must be any elemets for uninstall
                throw new OperationException(OperationException.ERROR_TYPE.UNINSTALL,
                        UninstallStep_NullSupport_NullElements());
            }
            throw new OperationException(OperationException.ERROR_TYPE.UNINSTALL,
                    "OperationSupport cannot be null because OperationContainer "
                    + "contains elements: " + model.getBaseContainer().listAll() + " and invalid elements " + model.getBaseContainer().listInvalid());
        }
        ProgressHandle handle = null;
        switch (model.getOperation ()) {
            case UNINSTALL :
                handle = ProgressHandleFactory.createHandle(UninstallStep_ProgressName_Uninstall());
                break;
            case ENABLE :
                handle = ProgressHandleFactory.createHandle(UninstallStep_ProgressName_Activate());
                break;
            case DISABLE :
                handle = ProgressHandleFactory.createHandle(UninstallStep_ProgressName_Deactivate());
                break;
            default:
                assert false : "Unknown OperationType " + model.getOperation ();
        }
        
        JComponent progressComponent = ProgressHandleFactory.createProgressComponent (handle);
        JLabel mainLabel = ProgressHandleFactory.createMainLabelComponent (handle);
        JLabel detailLabel = ProgressHandleFactory.createDetailLabelComponent (handle);
        model.modifyOptionsForDisabledCancel (wd);
        
        panel.waitAndSetProgressComponents (mainLabel, progressComponent, detailLabel);
        
        Restarter r = null;
        try {
            r = support.doOperation (handle);
            panel.waitAndSetProgressComponents(mainLabel, progressComponent, new JLabel(UninstallStep_Done()));
        } catch (OperationException ex) {
            err.log (Level.INFO, ex.getMessage (), ex);
            panel.waitAndSetProgressComponents(mainLabel, progressComponent,
                    new JLabel(UninstallStep_Failed(ex.getLocalizedMessage())));
            throw ex;
        }
        return r;
    }
}