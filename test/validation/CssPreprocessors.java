package org.netbeans.modules.web.common.api;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.netbeans.api.annotations.common.CheckForNull;
import org.netbeans.api.annotations.common.NonNull;
import org.netbeans.api.annotations.common.NullAllowed;
import org.netbeans.api.project.Project;
import org.netbeans.modules.web.common.cssprep.CssPreprocessorAccessor;
import org.netbeans.modules.web.common.cssprep.CssPreprocessorsAccessor;
import org.netbeans.modules.web.common.spi.CssPreprocessorImplementation;
import org.netbeans.modules.web.common.spi.CssPreprocessorImplementationListener;
import org.openide.filesystems.FileObject;
import org.openide.util.Lookup;
import org.openide.util.LookupEvent;
import org.openide.util.LookupListener;
import org.openide.util.Parameters;
import org.openide.util.RequestProcessor;
import org.openide.util.lookup.Lookups;
public final class CssPreprocessors {
    public static final String PREPROCESSORS_PATH = "CSS/PreProcessors";
    private static final RequestProcessor RP = new RequestProcessor(CssPreprocessors.class.getName(), 2);
    private static final Lookup.Result<CssPreprocessorImplementation> PREPROCESSORS = Lookups.forPath(PREPROCESSORS_PATH).lookupResult(CssPreprocessorImplementation.class);
    private static final CssPreprocessors INSTANCE = new CssPreprocessors();
    private final List<CssPreprocessor> preprocessors = new CopyOnWriteArrayList<>();
    final CssPreprocessorsListener.Support listenersSupport = new CssPreprocessorsListener.Support();
    private final PreprocessorImplementationsListener preprocessorImplementationsListener = new PreprocessorImplementationsListener();

    void reinitProcessors() {
        synchronized (preprocessors) {
            clearProcessors();
            assert preprocessors.isEmpty() : "Empty preprocessors expected but: " + preprocessors;
            preprocessors.addAll(map(PREPROCESSORS.allInstances()));
            for (CssPreprocessor cssPreprocessor : preprocessors) {
                cssPreprocessor.getDelegate().addCssPreprocessorListener(preprocessorImplementationsListener);
            }
        }
        listenersSupport.firePreprocessorsChanged();
    }

}