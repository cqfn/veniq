package org.openide.awt;
import java.awt.Component;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import javax.swing.Action;
import javax.swing.Icon;
import javax.swing.ImageIcon;
import javax.swing.JComponent;
import javax.swing.JMenu;
import javax.swing.JMenuItem;
import javax.swing.JPopupMenu;
import javax.swing.JSeparator;
import javax.swing.UIManager;
import org.openide.filesystems.FileObject;
import org.openide.util.ImageUtilities;
import org.openide.util.Utilities;
import org.openide.util.actions.Presenter;
class DynaMenuModel {
    private static final Icon BLANK_ICON = new ImageIcon(ImageUtilities.loadImage("org/openide/loaders/empty.gif"));
    private List<JComponent> menuItems;
    private HashMap<DynamicMenuContent, JComponent[]> actionToMenuMap;
    private boolean isWithIcons = false;
    public DynaMenuModel() {
        actionToMenuMap = new HashMap<DynamicMenuContent, JComponent[]>();
    }
    public void loadSubmenu(List<Object> cInstances, JMenu m, boolean remove, Map<Object,FileObject> cookiesToFiles) {
        boolean addSeparator = false;
        Icon curIcon = null;
        Iterator it = cInstances.iterator();
        menuItems = new ArrayList<JComponent>(cInstances.size());
        actionToMenuMap.clear();
        while (it.hasNext()) {
            Object obj = it.next();
            if (obj instanceof Action) {
                FileObject file = cookiesToFiles.get(obj);
                if (file != null) {
                    AcceleratorBinding.setAccelerator((Action) obj, file);
                }
            }
            if (obj instanceof Presenter.Menu) {
                obj = ((Presenter.Menu)obj).getMenuPresenter();
            }
            if (obj instanceof DynamicMenuContent) {
                if(addSeparator) {
                    menuItems.add(null);
                    addSeparator = false;
                }
                DynamicMenuContent mn = (DynamicMenuContent)obj;
                JComponent[] itms = convertArray(mn.getMenuPresenters());
                actionToMenuMap.put(mn, itms);
                Iterator itx = Arrays.asList(itms).iterator();
                while (itx.hasNext()) {
                    JComponent comp = (JComponent)itx.next();
                    menuItems.add(comp);
                    isWithIcons = checkIcon(comp, isWithIcons);
                }
                continue;
            }
            if (obj instanceof JMenuItem) {
                if(addSeparator) {
                    menuItems.add(null);
                    addSeparator = false;
                }
                isWithIcons = checkIcon(obj, isWithIcons);
                menuItems.add((JMenuItem)obj);
            } else if (obj instanceof JSeparator) {
                addSeparator = menuItems.size() > 0;
            } else if (obj instanceof Action) {
                if(addSeparator) {
                    menuItems.add(null);
                    addSeparator = false;
                }
                Action a = (Action)obj;
                Actions.MenuItem item = new Actions.MenuItem(a, true);
                isWithIcons = checkIcon(item, isWithIcons);
                actionToMenuMap.put(item, new JComponent[] {item});
                menuItems.add(item);
            }
        }
        if (isWithIcons) {
            menuItems = alignVertically(menuItems);
        }
        if (remove) {
            m.removeAll();
        }
        JComponent curItem = null;
        boolean wasSeparator = false;
        for (Iterator<JComponent> iter = menuItems.iterator(); iter.hasNext(); ) {
            curItem = iter.next();
            if (curItem == null) {
                JMenu menu = new JMenu();
                menu.addSeparator();
                curItem = (JSeparator)menu.getPopupMenu().getComponent(0);
            }
            m.add(curItem);
            boolean isSeparator = curItem instanceof JSeparator;
            if (isSeparator && wasSeparator) {
                curItem.setVisible(false);
            }
            if (!(curItem instanceof InvisibleMenuItem)) {
                wasSeparator = isSeparator;
            }
        }
    }

}