#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2024 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# standard library imports
import os
import random
import time
import threading

# third-party imports
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class BleachBitWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="BleachBit Prototype of Next-Generation GUI")
        self.set_default_size(1000, 400)

        # Create a vertical box to hold the menubar, toolbar, and panes.
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        self.create_menubar(vbox)
        self.create_toolbar(vbox)

        # Split the window horizontally into two panes
        paned = Gtk.Paned()
        paned.set_position(200)
        paned.set_wide_handle(True)
        vbox.pack_start(paned, True, True, 0)
        self.create_options_pane(paned)
        self.create_results_pane(paned)

    def create_menubar(self, vbox):
        """Create a menu bar"""
        menubar = Gtk.MenuBar()

        menu_items = [
            ("File", [
                ("Shred file", None),
                ("Shred folder", None),
                ("Wipe free space", None),
                ("Make chaff", None),
                ("Quit", None),
            ]),
            ("Edit", [
                ("Preferences", None)
            ]),
            ("Help", [
                ("System information", None),
                ("Help", None),
                ("About", None)
            ])
        ]
        for label, submenu_items in menu_items:
            menu = Gtk.Menu()
            for i, (submenu_label, submenu_func) in enumerate(submenu_items):
                item = Gtk.MenuItem()
                item.set_label(submenu_label)
                if submenu_func is not None:
                    item.connect("activate", submenu_func)
                menu.append(item)
            item = Gtk.MenuItem()
            item.set_label(label)
            item.set_submenu(menu)
            menubar.append(item)
        vbox.pack_start(menubar, False, False, 0)

    def create_options_pane(self, paned):
        """Create a pane for cleaning options

        The pane contains a search entry and a two-level TreeView.
        Example options are Firefox: History and Chrome: History.
        """
        # Create a vertical box to hold a search entry and a TreeView
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Create a search box to filter the options.
        self.search_entry = Gtk.Entry(width_chars=20)
        self.search_entry.set_placeholder_text("Search")
        self.search_entry_text = None
        self.search_entry.connect("changed", self.on_search_entry_changed)

        vbox.pack_start(self.search_entry, False, False, 0)

        # Create a TreeView to display the available cleaning options
        self.treestore_options = Gtk.TreeStore(str, bool)
        self.treeview_options = Gtk.TreeView(self.treestore_options)
        self.option_filter = self.treestore_options.filter_new()
        self.option_filter.set_visible_func(self.on_search_changed_filter)
        self.treeview_options.set_model(self.option_filter)
        vbox.pack_start(self.treeview_options, True, True, 0)

        # Create columns for the options
        options_column = Gtk.TreeViewColumn("Option")
        options_renderer = Gtk.CellRendererText()
        options_column.pack_start(options_renderer, True)
        options_column.add_attribute(options_renderer, "text", 0)
        self.treeview_options.append_column(options_column)

        selected_column = Gtk.TreeViewColumn("Selected")
        selected_renderer = Gtk.CellRendererToggle()
        selected_column.pack_start(selected_renderer, True)
        selected_column.add_attribute(selected_renderer, "active", 1)
        self.treeview_options.append_column(selected_column)

        # Add some sample data
        self.populate_options_pane()

        paned.add1(vbox)

    def on_search_entry_changed(self, entry):
        """Callback function for user typing in the options search box."""
        self.search_entry_text = self.search_entry.get_text()
        self.option_filter.refilter()

    def on_search_changed_filter(self, model, iter, data):
        """Callback function for each row in the options TreeView.

        This is called for row to set its visibility.

         Logic is as follows:
         * If the search box is empty, show all rows.
         * Searches are case insenitive.
         * If the search box matches a child (e.g., cookies, cache), show this child and its parent. This may hide its brothers such searching for "cookie" will hide "cache."
         * If the search box matches a parent (e.g., Firefox, Chrome), show this parent and all its children. 
        """

        current_row = model.get_value(iter, 0)
        print(f'Search changed filter: {
              self.search_entry_text} current row: {current_row}')
        if not self.search_entry_text:
            return True
        if current_row.lower().find(self.search_entry_text.lower()) != -1:
            return True

        parent_iter = model.iter_parent(iter)
        if parent_iter is not None:
            parent_name = model.get_value(parent_iter, 0)
            if parent_name.lower().find(self.search_entry_text.lower()) != -1:
                return True
        # If the search box matches a child, show this child and its parent
        child_iter = model.iter_children(iter)
        while child_iter is not None:
            child_name = model.get_value(child_iter, 0)
            if child_name.lower().find(self.search_entry_text.lower()) != -1:
                return True
            child_iter = model.iter_next(child_iter)
        return False

    def populate_options_pane(self):
        """Create example cleaners and options

        This is example data for demonstration.
        """
        browser_options = ["Cache", "History",
                           "Cookies", "Sessions", "Passwords"]
        sample_data = {
            "Firefox": browser_options,
            "Chrome": browser_options,
            "Edge": browser_options,
            "System": ['Cache', 'Clipboard', 'Custom', 'Logs', 'Temporary files', 'Trash']
        }
        for parent, children in sample_data.items():
            parent_iter = self.treestore_options.append(None, [parent, True])
            for child in children:
                self.treestore_options.append(parent_iter, [child, True])

    def create_toolbar(self, vbox):
        """Create the main toolbar with buttons"""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH)  # Show text and icon.

        preview_button = Gtk.ToolButton(
            stock_id=Gtk.STOCK_REFRESH, label="Preview")
        preview_button.connect("clicked", self.on_preview_clicked)
        toolbar.insert(preview_button, 0)

        clean_button = Gtk.ToolButton(stock_id=Gtk.STOCK_CLEAR, label="Clean")
        clean_button.connect("clicked", self.on_clean_clicked)
        toolbar.insert(clean_button, 1)

        self.abort_button = Gtk.ToolButton(
            stock_id=Gtk.STOCK_STOP, label="Abort")
        self.abort_button.set_sensitive(False)
        toolbar.insert(self.abort_button, 2)

        self.whitelist_button = Gtk.ToolButton(
            stock_id=Gtk.STOCK_ADD, label="Whitelist")
        self.whitelist_button.connect("clicked", self.on_whitelist_clicked)
        toolbar.insert(self.whitelist_button, 3)
        self.whitelist_button.set_sensitive(False)

        vbox.pack_start(toolbar, False, False, 0)

    def create_results_pane(self, paned):
        """Create a pane for search results

        The search pane contains a search box and a TreeView with list of files

        Args:
            paned (Gtk.Paned): The parent pane

        Returns:
            None
        """
        # Create a vertical box to hold the search entry and the scrolled window
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        paned.add2(vbox)

        # Create a search box
        search_entry = Gtk.Entry(width_chars=100)
        search_entry.set_placeholder_text("Search")
        # search_entry.connect("changed", self.on_results_search_changed)
        vbox.pack_start(search_entry, False, False, 0)

        # Create a TreeView to display the cleaning results
        self.treeview = Gtk.TreeView()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.treeview)
        vbox.pack_start(scrolled, True, True, 0)

        # Create a ListStore to hold the data
        self.liststore = Gtk.ListStore(str, str, str, int, str)
        self.treeview.set_model(self.liststore)

        # Create columns: cleaner, option, filename, file size, action.
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Cleaner", renderer, text=0)
        column.set_sort_column_id(0)
        self.treeview.append_column(column)

        column = Gtk.TreeViewColumn("Option", renderer, text=1)
        column.set_sort_column_id(1)
        self.treeview.append_column(column)

        column = Gtk.TreeViewColumn("Filename", renderer, text=2)
        column.set_sort_column_id(2)
        self.treeview.append_column(column)

        column = Gtk.TreeViewColumn("File size (B)", renderer, text=3)
        column.set_sort_column_id(3)
        self.treeview.append_column(column)

        column = Gtk.TreeViewColumn("Action", renderer, text=4)
        column.set_sort_column_id(4)
        self.treeview.append_column(column)

        # Allow user to seelct multple rows for whitelisting.
        self.treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        # Add a context menu.
        self.treeview.connect("button-press-event",
                              self.on_file_result_context_menu)

        self.treeview.get_selection().connect("changed", self.on_selection_changed)

    def on_selection_changed(self, selection):
        """Enable whitelist button on toolbar when 1+ rows are selected"""
        model, paths = selection.get_selected_rows()
        sensitive = len(paths) > 0
        self.whitelist_button.set_sensitive(sensitive)

    def on_copy_path_activated(self, widget, filename):
        """Copy filename to clipboard"""
        from gi.repository import Gdk
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(filename, -1)

    def on_file_result_context_menu(self, widget, event):
        """Show a context menu for file result"""
        # 3 is the right mouse button
        if not event.button == 3:
            return
        selection = self.treeview.get_selection()
        model, pathlist = selection.get_selected_rows()
        for path in pathlist:
            tree_iter = model.get_iter(path)
            filename = model.get_value(tree_iter, 2)
            menu = Gtk.Menu()
            copy_path_item = Gtk.MenuItem.new_with_label("Copy path")
            copy_path_item.connect(
                "activate", self.on_copy_path_activated, filename)
            menu.append(copy_path_item)
            open_file_location_item = Gtk.MenuItem.new_with_label(
                "Open file location")
            copy_path_item.connect(
                "activate", self.on_copy_path_activated, filename)

            menu.append(open_file_location_item)
            whitelist_item = Gtk.MenuItem.new_with_label("Whitelist")
            # whitelist_item.connect("activate", self.on_whitelist_activated, filename)
            menu.append(whitelist_item)
            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)

    def populate_data(self, is_delete=True):
        """Launch a thread to populate the data"""
        thread = threading.Thread(
            target=self._populate_data, args=(is_delete,))
        thread.start()

    def _populate_data(self, is_delete=True):
        """In background thread, populate the data"""
        self.abort_button.set_sensitive(True)
        num_files = random.randint(5, 50)
        for i in range(num_files):
            cleaner_name = random.choice(["Chrome", "Firefox", "Edge"])
            option_name = random.choice(
                ["Cache", "History", "Cookies", "Sessions", "Passwords"])
            filename = os.path.join(os.path.expanduser(
                "~"), ".config", cleaner_name, option_name, str(random.randint(0, 100)))
            if option_name == 'Cache':
                filename = os.path.join(os.path.expanduser(
                    "~"), ".cache", cleaner_name, str(random.randint(0, 100)))
            size = random.randint(0, 10000)
            result_random = random.random()
            if is_delete:
                if result_random < 0.05:
                    result = "error"
                elif result_random < 0.15:
                    result = "deleted"
                else:
                    result = "shred"
            else:
                result = ""

            # Sleep simulates waiting for disk I/O.
            sleep_time_sec = random.uniform(0.01, 0.2)
            if not is_delete:
                sleep_time_sec = sleep_time_sec/10
            time.sleep(sleep_time_sec)
            self.liststore.append(
                [cleaner_name, option_name, filename, size, result])
        self.abort_button.set_sensitive(False)

    def on_preview_clicked(self, button):
        # Clear the previous cleaning results and populate a new list of files
        self.liststore.clear()
        self.populate_data(is_delete=False)

    def on_clean_clicked(self, button):
        # Clear the previous cleaning results and populate a new list of files
        self.liststore.clear()
        self.populate_data(is_delete=True)

    def on_whitelist_clicked(self, button):
        # Get the selected rows
        selection = self.treeview.get_selection()
        model, paths = selection.get_selected_rows()
        for path in paths:
            # Get the filename
            filename = model[path][2]
            print(f"Whitelisted: {filename}")


if __name__ == "__main__":
    win = BleachBitWindow()
    win.set_icon_from_file("bleachbit.png")
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
