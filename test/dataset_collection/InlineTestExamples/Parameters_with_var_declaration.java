package org.netbeans.jellytools.modules.form.properties.editors;
import org.netbeans.jellytools.Bundle;
import org.netbeans.jemmy.operators.JButtonOperator;
import org.netbeans.jemmy.operators.JComboBoxOperator;
import org.netbeans.jemmy.operators.JEditorPaneOperator;
import org.netbeans.jemmy.operators.JLabelOperator;
import org.netbeans.jemmy.operators.JRadioButtonOperator;
import org.netbeans.jemmy.operators.JTextFieldOperator;
public class ParametersPickerOperator extends FormCustomEditorOperator {
    private JLabelOperator _lblGetParameterFrom;
    private JRadioButtonOperator _rbComponent;
    private JComboBoxOperator _cboComponent;
    private JRadioButtonOperator _rbProperty;
    private JTextFieldOperator _txtProperty;
    private JButtonOperator _btSelectProperty;
    private JRadioButtonOperator _rbMethodCall;
    private JTextFieldOperator _txtMethodCall;
    private JButtonOperator _btSelectMethod;
    private JRadioButtonOperator _rbUserCode;
    private JEditorPaneOperator _txtUserCode;
    public ParametersPickerOperator(String propertyName) {
        super(propertyName);
    }
    public JLabelOperator lblGetParameterFrom() {
        if(_lblGetParameterFrom == null) {
            _lblGetParameterFrom = new JLabelOperator(this,
                            Bundle.getString("org.netbeans.modules.form.Bundle",
                                             "ConnectionCustomEditor.jLabel1.text"));
        }
        return _lblGetParameterFrom;
    }
    public JRadioButtonOperator rbComponent() {
        if(_rbComponent == null) {
            _rbComponent = new JRadioButtonOperator(this,
                            Bundle.getStringTrimmed("org.netbeans.modules.form.Bundle",
                                                    "ConnectionCustomEditor.beanRadio.text"));
        }
        return _rbComponent;
    }
    public JComboBoxOperator cboComponent() {
        if(_cboComponent == null) {
            _cboComponent = new JComboBoxOperator(this, 0);
        }
        return _cboComponent;
    }
    public JRadioButtonOperator rbProperty() {
        if(_rbProperty == null) {
            _rbProperty = new JRadioButtonOperator(this,
                            Bundle.getStringTrimmed("org.netbeans.modules.form.Bundle",
                                                    "ConnectionCustomEditor.propertyRadio.text"));
        }
        return _rbProperty;
    }
    public JTextFieldOperator txtProperty() {
        if(_txtProperty == null) {
            _txtProperty = new JTextFieldOperator(this, 0);
        }
        return _txtProperty;
    }
    public JButtonOperator btSelectProperty() {
        if(_btSelectProperty == null) {
            _btSelectProperty = new JButtonOperator(this, "...", 0);
        }
        return _btSelectProperty;
    }
    public JRadioButtonOperator rbMethodCall() {
        if(_rbMethodCall == null) {
            _rbMethodCall = new JRadioButtonOperator(this,
                            Bundle.getStringTrimmed("org.netbeans.modules.form.Bundle",
                                                    "ConnectionCustomEditor.methodRadio.text"));
        }
        return _rbMethodCall;
    }
    public JTextFieldOperator txtMethodCall() {
        if(_txtMethodCall==null) {
            _txtMethodCall = new JTextFieldOperator(this, 1);
        }
        return _txtMethodCall;
    }
    public JButtonOperator btSelectMethod() {
        if(_btSelectMethod == null) {
            _btSelectMethod = new JButtonOperator(this, "...", 1);
        }
        return _btSelectMethod;
    }
    public void component() {
        rbComponent().push();
    }
    public void setComponent(String item) {
        cboComponent().setSelectedItem(item);
    }
    public void property() {
        rbProperty().push();
    }
    public void selectProperty() {
        btSelectProperty().pushNoBlock();
    }
    public void methodCall() {
        rbMethodCall().push();
    }
    public void selectMethod() {
        btSelectMethod().pushNoBlock();
    }
    public void verify() {
        lblGetParameterFrom();
        txtMethodCall();
        txtProperty();
        rbComponent();
        rbMethodCall();
        rbProperty();
        btSelectMethod();
        if(_btSelectProperty == null) {
            _btSelectProperty = new JButtonOperator(this, "...", 0);
        }
        JButtonOperator jbuttonoperator = _btSelectProperty;
        _cboComponent = cboComponent();
        super.verify();
    }
}