import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pyodbc
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phonebook.log'),
        logging.StreamHandler()
    ]
)


class PhoneBookApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Phonebook - Phone Database")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)

        # Default theme
        self.current_theme = "dark"

        # Database connection
        self.setup_database()

        # UI setup
        self.setup_ui()

        # Load contacts
        self.load_contacts()

        logging.info("Phonebook application started")

    def setup_database(self):
        """Connect to SQL Server database"""
        try:
            # Database connection settings
            server = 'localhost'
            database = 'phone'  
            username = ''
            password = ''

            # Connection string
            if username and password:
                connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
            else:
                connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'

            self.conn = pyodbc.connect(connection_string)
            self.cursor = self.conn.cursor()

            # Create table if not exists
            self.create_table()

            logging.info("Database connection established")
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            messagebox.showerror("Error", f"Database connection error: {e}")

    def create_table(self):
        """Create contacts table in database"""
        try:
            create_table_query = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='contacts' AND xtype='U')
            CREATE TABLE contacts (
                id INT IDENTITY(1,1) PRIMARY KEY,
                first_name NVARCHAR(50) NOT NULL,
                last_name NVARCHAR(50) NOT NULL,
                phone NVARCHAR(20) NOT NULL,
                email NVARCHAR(100),
                address NVARCHAR(255),
                company NVARCHAR(100),
                notes NTEXT,
                created_date DATETIME DEFAULT GETDATE(),
                modified_date DATETIME DEFAULT GETDATE()
            )
            """
            self.cursor.execute(create_table_query)
            self.conn.commit()
            logging.info("Contacts table created/verified")
        except Exception as e:
            logging.error(f"Table creation error: {e}")

    def setup_ui(self):
        """Create user interface"""
        # Create menu bar
        self.create_menu()

        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create toolbar
        self.create_toolbar()

        # Search panel
        self.create_search_panel()

        # Contacts display panel
        self.create_contacts_panel()

        # Details panel
        self.create_details_panel()

        # Apply theme
        self.apply_theme()

    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show All Contacts", command=self.load_contacts)
        view_menu.add_separator()
        view_menu.add_command(label="Dark Theme", command=lambda: self.change_theme("dark"))
        view_menu.add_command(label="Light Theme", command=lambda: self.change_theme("light"))

        # About menu
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="About", command=self.show_about)

    def create_toolbar(self):
        """Create toolbar"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Toolbar buttons
        ttk.Button(toolbar, text="Add New", command=self.add_contact).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Edit", command=self.edit_contact).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Delete", command=self.delete_contact).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Show Details", command=self.show_details).pack(side=tk.RIGHT, padx=5)

        # Contacts count label
        self.contacts_count_label = ttk.Label(toolbar, text="Contacts: 0")
        self.contacts_count_label.pack(side=tk.LEFT)

    def create_search_panel(self):
        """Create search panel"""
        search_frame = ttk.LabelFrame(self.main_frame, text="Search", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 10))

        # Search fields
        ttk.Label(search_frame, text="First Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.search_first_name = ttk.Entry(search_frame, width=20)
        self.search_first_name.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(search_frame, text="Last Name:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.search_last_name = ttk.Entry(search_frame, width=20)
        self.search_last_name.grid(row=0, column=3, padx=(0, 10))

        ttk.Label(search_frame, text="Phone:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.search_phone = ttk.Entry(search_frame, width=20)
        self.search_phone.grid(row=0, column=5, padx=(0, 10))

        # Search buttons
        ttk.Button(search_frame, text="Search", command=self.search_contacts).grid(row=0, column=6, padx=(10, 0))
        ttk.Button(search_frame, text="Clear", command=self.clear_search).grid(row=0, column=7, padx=(5, 0))

    def create_contacts_panel(self):
        """Create contacts display panel"""
        contacts_frame = ttk.LabelFrame(self.main_frame, text="Contacts", padding="10")
        contacts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview for contacts - FIXED: Remove ID column from display
        columns = ("First Name", "Last Name", "Phone", "Email", "Company")
        self.contacts_tree = ttk.Treeview(contacts_frame, columns=columns, show="headings", height=15)

        # Configure columns - FIXED: No ID column in display
        self.contacts_tree.heading("First Name", text="First Name")
        self.contacts_tree.heading("Last Name", text="Last Name")
        self.contacts_tree.heading("Phone", text="Phone")
        self.contacts_tree.heading("Email", text="Email")
        self.contacts_tree.heading("Company", text="Company")

        # Column widths
        self.contacts_tree.column("First Name", width=120)
        self.contacts_tree.column("Last Name", width=120)
        self.contacts_tree.column("Phone", width=120)
        self.contacts_tree.column("Email", width=150)
        self.contacts_tree.column("Company", width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(contacts_frame, orient=tk.VERTICAL, command=self.contacts_tree.yview)
        self.contacts_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self.contacts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Selection event
        self.contacts_tree.bind("<<TreeviewSelect>>", self.on_contact_select)

        # Store contact IDs separately
        self.contact_ids = {}

    def create_details_panel(self):
        """Create contact details panel - IMPROVED"""
        details_frame = ttk.LabelFrame(self.main_frame, text="Contact Details - Complete Information", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=False)

        # Create a better details display
        details_container = ttk.Frame(details_frame)
        details_container.pack(fill=tk.BOTH, expand=True)

        # Use Text widget with better formatting
        self.details_text = scrolledtext.ScrolledText(
            details_container,
            height=10,
            state=tk.DISABLED,
            font=('Arial', 10),
            wrap=tk.WORD
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add some initial help text
        self.details_text.config(state=tk.NORMAL)
        self.details_text.insert(1.0, "Select a contact from the list above to view complete details...")
        self.details_text.config(state=tk.DISABLED)

    def apply_theme(self):
        """Apply theme to UI"""
        if self.current_theme == "dark":
            # Dark theme colors
            bg_color = "#2e2e2e"
            fg_color = "#ffffff"
            entry_bg = "#404040"
            entry_fg = "#ffffff"
            tree_bg = "#404040"
            tree_fg = "#ffffff"
            tree_selected = "#0078d7"
        else:
            # Light theme colors
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            entry_bg = "#ffffff"
            entry_fg = "#000000"
            tree_bg = "#ffffff"
            tree_fg = "#000000"
            tree_selected = "#0078d7"

        # Apply colors to widgets
        self.root.configure(bg=bg_color)
        self.main_frame.configure(style="TFrame")

        # Create style for widgets
        style = ttk.Style()
        style.theme_use('clam')

        # Configure style for dark/light theme
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TButton", background=bg_color, foreground=fg_color)
        style.configure("TEntry", fieldbackground=entry_bg, foreground=entry_fg)
        style.configure("TScrollbar", background=bg_color, troughcolor=bg_color)
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)

        # Configure Treeview
        style.configure("Treeview",
                        background=tree_bg,
                        foreground=tree_fg,
                        fieldbackground=tree_bg)
        style.map("Treeview", background=[('selected', tree_selected)])

        # Configure ScrolledText
        self.details_text.configure(bg=tree_bg, fg=tree_fg, insertbackground=fg_color)

    def change_theme(self, theme):
        """Change application theme"""
        self.current_theme = theme
        self.apply_theme()
        logging.info(f"Theme changed to {theme}")

    def load_contacts(self):
        """Load all contacts from database - FIXED"""
        try:
            # Clear Treeview and contact_ids
            for item in self.contacts_tree.get_children():
                self.contacts_tree.delete(item)
            self.contact_ids.clear()

            # Execute query
            query = "SELECT id, first_name, last_name, phone, email, company FROM contacts ORDER BY last_name, first_name"
            self.cursor.execute(query)
            contacts = self.cursor.fetchall()

            # Add contacts to Treeview and store IDs
            for contact in contacts:
                contact_id = contact[0]
                display_values = contact[1:]  # Skip ID for display
                item_id = self.contacts_tree.insert("", tk.END, values=display_values)

                # Store contact ID with tree item ID
                self.contact_ids[item_id] = contact_id

            # Update count label
            self.contacts_count_label.config(text=f"Contacts: {len(contacts)}")

            # Clear details
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, "Select a contact from the list above to view complete details...")
            self.details_text.config(state=tk.DISABLED)

            logging.info(f"Loaded {len(contacts)} contacts")
        except Exception as e:
            logging.error(f"Error loading contacts: {e}")
            messagebox.showerror("Error", f"Error loading contacts: {e}")

    def search_contacts(self):
        """Search contacts based on criteria - FIXED"""
        try:
            # Get search criteria
            first_name = self.search_first_name.get().strip()
            last_name = self.search_last_name.get().strip()
            phone = self.search_phone.get().strip()

            # Build search query
            query = "SELECT id, first_name, last_name, phone, email, company FROM contacts WHERE 1=1"
            params = []

            if first_name:
                query += " AND first_name LIKE ?"
                params.append(f"%{first_name}%")

            if last_name:
                query += " AND last_name LIKE ?"
                params.append(f"%{last_name}%")

            if phone:
                query += " AND phone LIKE ?"
                params.append(f"%{phone}%")

            query += " ORDER BY last_name, first_name"

            # Execute query
            self.cursor.execute(query, params)
            contacts = self.cursor.fetchall()

            # Clear Treeview and contact_ids
            for item in self.contacts_tree.get_children():
                self.contacts_tree.delete(item)
            self.contact_ids.clear()

            # Add search results
            for contact in contacts:
                contact_id = contact[0]
                display_values = contact[1:]  # Skip ID for display
                item_id = self.contacts_tree.insert("", tk.END, values=display_values)
                self.contact_ids[item_id] = contact_id

            # Update count
            self.contacts_count_label.config(text=f"Contacts: {len(contacts)}")

            logging.info(f"Search found {len(contacts)} contacts")

        except Exception as e:
            logging.error(f"Search error: {e}")
            messagebox.showerror("Error", f"Search error: {e}")

    def clear_search(self):
        """Clear search fields and show all contacts"""
        self.search_first_name.delete(0, tk.END)
        self.search_last_name.delete(0, tk.END)
        self.search_phone.delete(0, tk.END)
        self.load_contacts()
        logging.info("Search cleared")

    def on_contact_select(self, event):
        """Handle contact selection - FIXED"""
        selection = self.contacts_tree.selection()
        if selection:
            item_id = selection[0]
            contact_id = self.contact_ids.get(item_id)
            if contact_id:
                self.display_contact_details(contact_id)

    def display_contact_details(self, contact_id):
        """Display detailed contact information - IMPROVED"""
        try:
            query = "SELECT * FROM contacts WHERE id = ?"
            self.cursor.execute(query, (contact_id,))
            contact = self.cursor.fetchone()

            if contact:
                # Format details better
                details = f"""📋 CONTACT DETAILS
─────────────────────────────
👤 Name: {contact[1]} {contact[2]}
📞 Phone: {contact[3]}
📧 Email: {contact[4] if contact[4] else 'Not specified'}
🏠 Address: {contact[5] if contact[5] else 'Not specified'}
🏢 Company: {contact[6] if contact[6] else 'Not specified'}

📝 Notes:
{contact[7] if contact[7] else 'No notes available'}

📅 Created: {contact[8]}
🔄 Modified: {contact[9]}
─────────────────────────────
Contact ID: {contact[0]}"""

                self.details_text.config(state=tk.NORMAL)
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(1.0, details)
                self.details_text.config(state=tk.DISABLED)

                logging.info(f"Displayed details for contact ID: {contact_id}")
        except Exception as e:
            logging.error(f"Error displaying contact details: {e}")
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, f"Error loading contact details: {e}")
            self.details_text.config(state=tk.DISABLED)

    def add_contact(self):
        """Open add contact dialog"""
        self.contact_dialog("Add New Contact")

    def edit_contact(self):
        """Open edit contact dialog - FIXED"""
        selection = self.contacts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a contact to edit")
            return

        item_id = selection[0]
        contact_id = self.contact_ids.get(item_id)

        if contact_id:
            self.contact_dialog("Edit Contact", contact_id)
        else:
            messagebox.showerror("Error", "Could not find contact ID")

    def contact_dialog(self, title, contact_id=None):
        """Create contact add/edit dialog - IMPROVED"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x500")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Form fields
        fields_frame = ttk.Frame(dialog, padding="20")
        fields_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(fields_frame, text="First Name:*").grid(row=0, column=0, sticky=tk.W, pady=5)
        first_name_entry = ttk.Entry(fields_frame, width=30)
        first_name_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="Last Name:*").grid(row=1, column=0, sticky=tk.W, pady=5)
        last_name_entry = ttk.Entry(fields_frame, width=30)
        last_name_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="Phone:*").grid(row=2, column=0, sticky=tk.W, pady=5)
        phone_entry = ttk.Entry(fields_frame, width=30)
        phone_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="Email:").grid(row=3, column=0, sticky=tk.W, pady=5)
        email_entry = ttk.Entry(fields_frame, width=30)
        email_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="Address:").grid(row=4, column=0, sticky=tk.W, pady=5)
        address_entry = ttk.Entry(fields_frame, width=30)
        address_entry.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="Company:").grid(row=5, column=0, sticky=tk.W, pady=5)
        company_entry = ttk.Entry(fields_frame, width=30)
        company_entry.grid(row=5, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="Notes:").grid(row=6, column=0, sticky=tk.NW, pady=5)
        notes_text = scrolledtext.ScrolledText(fields_frame, width=30, height=5)
        notes_text.grid(row=6, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Load data if editing
        if contact_id:
            try:
                query = "SELECT * FROM contacts WHERE id = ?"
                self.cursor.execute(query, (contact_id,))
                contact = self.cursor.fetchone()

                if contact:
                    first_name_entry.insert(0, contact[1])
                    last_name_entry.insert(0, contact[2])
                    phone_entry.insert(0, contact[3])
                    email_entry.insert(0, contact[4] if contact[4] else "")
                    address_entry.insert(0, contact[5] if contact[5] else "")
                    company_entry.insert(0, contact[6] if contact[6] else "")
                    notes_text.insert(1.0, contact[7] if contact[7] else "")
            except Exception as e:
                logging.error(f"Error loading contact for edit: {e}")
                messagebox.showerror("Error", f"Error loading contact: {e}")

        # Buttons
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X)

        def save_contact():
            try:
                # Get form data
                first_name = first_name_entry.get().strip()
                last_name = last_name_entry.get().strip()
                phone = phone_entry.get().strip()
                email = email_entry.get().strip()
                address = address_entry.get().strip()
                company = company_entry.get().strip()
                notes = notes_text.get(1.0, tk.END).strip()

                # Validation
                if not first_name or not last_name or not phone:
                    messagebox.showerror("Error", "First Name, Last Name, and Phone are required")
                    return

                if contact_id:
                    # Update existing contact
                    query = """UPDATE contacts 
                              SET first_name=?, last_name=?, phone=?, email=?, address=?, company=?, notes=?, modified_date=GETDATE()
                              WHERE id=?"""
                    params = (first_name, last_name, phone, email, address, company, notes, contact_id)
                    action = "updated"
                else:
                    # Insert new contact
                    query = """INSERT INTO contacts (first_name, last_name, phone, email, address, company, notes)
                              VALUES (?, ?, ?, ?, ?, ?, ?)"""
                    params = (first_name, last_name, phone, email, address, company, notes)
                    action = "added"

                self.cursor.execute(query, params)
                self.conn.commit()

                self.load_contacts()
                dialog.destroy()

                logging.info(f"Contact {action} successfully")
                messagebox.showinfo("Success", f"Contact {action} successfully")

            except Exception as e:
                logging.error(f"Error saving contact: {e}")
                messagebox.showerror("Error", f"Error saving contact: {e}")

        ttk.Button(button_frame, text="Save", command=save_contact).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def delete_contact(self):
        """Delete selected contact - FIXED"""
        selection = self.contacts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a contact to delete")
            return

        item_id = selection[0]
        contact_id = self.contact_ids.get(item_id)

        if not contact_id:
            messagebox.showerror("Error", "Could not find contact ID")
            return

        # Get contact name for confirmation
        item_values = self.contacts_tree.item(item_id, 'values')
        contact_name = f"{item_values[0]} {item_values[1]}"

        # Confirmation
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {contact_name}?"):
            try:
                query = "DELETE FROM contacts WHERE id = ?"
                self.cursor.execute(query, (contact_id,))
                self.conn.commit()

                self.load_contacts()

                logging.info(f"Contact {contact_name} (ID: {contact_id}) deleted")
                messagebox.showinfo("Success", "Contact deleted successfully")

            except Exception as e:
                logging.error(f"Error deleting contact: {e}")
                messagebox.showerror("Error", f"Error deleting contact: {e}")

    def show_details(self):
        """Show details of selected contact - FIXED"""
        selection = self.contacts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a contact to view details")
            return

        item_id = selection[0]
        contact_id = self.contact_ids.get(item_id)

        if contact_id:
            self.display_contact_details(contact_id)
        else:
            messagebox.showerror("Error", "Could not find contact details")

    def show_about(self):
        """Show about information"""
        about_text = """Advanced Phonebook Application

Version: 2.0 - Fixed Edition
Database: phone
Developed with Python and Tkinter

Fixed Issues:
- Delete contact error resolved
- Edit contact loading fixed  
- Show details working properly
- Better contact details display
- Improved error handling

© 2024 Phonebook App"""

        messagebox.showinfo("About", about_text)
        logging.info("About dialog displayed")


def main():
    """Main function to start the application"""
    try:
        root = tk.Tk()
        app = PhoneBookApp(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Application error: {e}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {e}")


if __name__ == "__main__":
    main()