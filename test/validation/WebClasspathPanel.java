package org.netbeans.modules.web.freeform.ui;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.util.List;
import javax.swing.DefaultListModel;
import javax.swing.JFileChooser;
import javax.swing.filechooser.FileFilter;
import org.netbeans.api.project.ant.FileChooser;
import org.netbeans.modules.ant.freeform.spi.support.Util;
import org.netbeans.modules.web.freeform.WebProjectGenerator;
import org.netbeans.spi.project.AuxiliaryConfiguration;
import org.netbeans.spi.project.support.ant.AntProjectHelper;
import org.netbeans.spi.project.support.ant.PropertyEvaluator;
import org.netbeans.spi.project.support.ant.PropertyUtils;
import org.openide.filesystems.FileUtil;
import org.openide.util.Exceptions;
import org.openide.util.HelpCtx;
import org.openide.util.NbBundle;
public class WebClasspathPanel extends javax.swing.JPanel implements HelpCtx.Provider {
    private DefaultListModel<String> listModel;
    private File projectFolder = null;
    private File nbProjectFolder;
    private File lastChosenFile = null;
    private boolean isSeparateClasspath = true;
    private boolean ignoreEvent;
    private static String JAVA_SOURCES_CLASSPATH
            = org.openide.util.NbBundle.getMessage(WebClasspathPanel.class, "LBL_JAVA_SOURCE_CLASSPATH");
    public WebClasspathPanel() {
        this(true);
    }
    ActionListener getCustomizerOkListener(final AntProjectHelper projectHelper) {
        return new ActionListener() {
            public void actionPerformed(ActionEvent arg0) {
                AuxiliaryConfiguration aux = Util.getAuxiliaryConfiguration(projectHelper);
                List<WebProjectGenerator.WebModule> l = WebProjectGenerator.getWebmodules(projectHelper, aux);
                if (l != null){
                    WebProjectGenerator.WebModule wm = (WebProjectGenerator.WebModule)l.get(0);
                    wm.classpath = getClasspath();
                    WebProjectGenerator.putWebModules(projectHelper, aux, l);
                }
                updateButtons();
            }
        };
    }
}