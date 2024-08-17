import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3

# Initialize the database
conn = sqlite3.connect('bank_system.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                account_type TEXT,
                balance REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                type TEXT,
                amount REAL,
                date TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )''')

conn.commit()

# User Account Management
class UserAccount:
    def __init__(self):
        self.current_user_id = None

    def create_account(self, username, password):
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login(self, username, password):
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        if user:
            self.current_user_id = user[0]
            return True
        return False

    def logout(self):
        self.current_user_id = None

    def get_current_user_id(self):
        return self.current_user_id

# Bank Account Management
class BankAccount:
    def __init__(self, user_id):
        self.user_id = user_id

    def create_account(self, account_type):
        c.execute("INSERT INTO accounts (user_id, account_type) VALUES (?, ?)", (self.user_id, account_type))
        conn.commit()

    def get_accounts(self):
        c.execute("SELECT id, account_type, balance FROM accounts WHERE user_id=?", (self.user_id,))
        return c.fetchall()

    def get_account(self, account_id):
        c.execute("SELECT balance FROM accounts WHERE id=?", (account_id,))
        return c.fetchone()[0]

    def deposit(self, account_id, amount):
        c.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, account_id))
        conn.commit()
        self.record_transaction(account_id, "Deposit", amount)

    def withdraw(self, account_id, amount):
        balance = self.get_account(account_id)
        if amount > balance:
            return False
        c.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, account_id))
        conn.commit()
        self.record_transaction(account_id, "Withdrawal", amount)
        return True

    def transfer(self, from_account_id, to_account_id, amount):
        if self.withdraw(from_account_id, amount):
            self.deposit(to_account_id, amount)
            return True
        return False

    def record_transaction(self, account_id, transaction_type, amount):
        c.execute("INSERT INTO transactions (account_id, type, amount, date) VALUES (?, ?, ?, datetime('now'))",
                  (account_id, transaction_type, amount))
        conn.commit()

    def get_transaction_history(self, account_id):
        c.execute("SELECT type, amount, date FROM transactions WHERE account_id=?", (account_id,))
        return c.fetchall()

# GUI Application
class BankApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Bank System")
        self.user_account = UserAccount()
        self.current_account_id = None

        self.login_frame = None
        self.main_frame = None

        self.show_login_screen()

    def show_login_screen(self):
        self.clear_frame()

        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=20)

        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0, pady=5)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0, pady=5)
        self.password_entry = tk.Entry(self.login_frame, show='*')
        self.password_entry.grid(row=1, column=1, pady=5)

        tk.Button(self.login_frame, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=5)
        tk.Button(self.login_frame, text="Create Account", command=self.create_account_screen).grid(row=3, column=0, columnspan=2, pady=5)

    def show_main_screen(self):
        self.clear_frame()

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(pady=20)

        tk.Button(self.main_frame, text="View Accounts", command=self.view_accounts).grid(row=0, column=0, pady=10)
        tk.Button(self.main_frame, text="Create Account", command=self.create_bank_account_screen).grid(row=1, column=0, pady=10)
        tk.Button(self.main_frame, text="Logout", command=self.logout).grid(row=2, column=0, pady=10)

    def view_accounts(self):
        self.clear_frame()

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(pady=20)

        accounts = BankAccount(self.user_account.get_current_user_id()).get_accounts()

        for idx, (account_id, account_type, balance) in enumerate(accounts):
            tk.Label(self.main_frame, text=f"{account_type} Account: ${balance:.2f}").grid(row=idx, column=0, pady=5)
            tk.Button(self.main_frame, text="Manage", command=lambda a_id=account_id: self.manage_account_screen(a_id)).grid(row=idx, column=1, pady=5)

        tk.Button(self.main_frame, text="Back", command=self.show_main_screen).grid(row=len(accounts) + 1, column=0, pady=10)

    def manage_account_screen(self, account_id):
        self.current_account_id = account_id
        self.clear_frame()

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(pady=20)

        tk.Button(self.main_frame, text="Deposit", command=self.deposit_screen).grid(row=0, column=0, pady=10)
        tk.Button(self.main_frame, text="Withdraw", command=self.withdraw_screen).grid(row=1, column=0, pady=10)
        tk.Button(self.main_frame, text="Transfer", command=self.transfer_screen).grid(row=2, column=0, pady=10)
        tk.Button(self.main_frame, text="Transaction History", command=self.view_transaction_history).grid(row=3, column=0, pady=10)
        tk.Button(self.main_frame, text="Back", command=self.view_accounts).grid(row=4, column=0, pady=10)

    def deposit_screen(self):
        amount = simpledialog.askfloat("Deposit", "Enter amount to deposit:")
        if amount:
            BankAccount(self.user_account.get_current_user_id()).deposit(self.current_account_id, amount)
            messagebox.showinfo("Success", "Deposit successful")
        self.manage_account_screen(self.current_account_id)

    def withdraw_screen(self):
        amount = simpledialog.askfloat("Withdraw", "Enter amount to withdraw:")
        if amount:
            success = BankAccount(self.user_account.get_current_user_id()).withdraw(self.current_account_id, amount)
            if success:
                messagebox.showinfo("Success", "Withdrawal successful")
            else:
                messagebox.showerror("Error", "Insufficient funds")
        self.manage_account_screen(self.current_account_id)

    def transfer_screen(self):
        accounts = BankAccount(self.user_account.get_current_user_id()).get_accounts()
        account_ids = [a_id for a_id, _, _ in accounts if a_id != self.current_account_id]

        if not account_ids:
            messagebox.showerror("Error", "No other accounts available for transfer.")
            return

        to_account_id = simpledialog.askinteger("Transfer", "Enter account ID to transfer to:")
        if to_account_id not in account_ids:
            messagebox.showerror("Error", "Invalid account ID")
            return

        amount = simpledialog.askfloat("Transfer", "Enter amount to transfer:")
        if amount:
            success = BankAccount(self.user_account.get_current_user_id()).transfer(self.current_account_id, to_account_id, amount)
            if success:
                messagebox.showinfo("Success", "Transfer successful")
            else:
                messagebox.showerror("Error", "Insufficient funds")
        self.manage_account_screen(self.current_account_id)

    def view_transaction_history(self):
        self.clear_frame()

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(pady=20)

        transactions = BankAccount(self.user_account.get_current_user_id()).get_transaction_history(self.current_account_id)

        for idx, (type, amount, date) in enumerate(transactions):
            tk.Label(self.main_frame, text=f"{type}: ${amount:.2f} on {date}").grid(row=idx, column=0, pady=5)

        tk.Button(self.main_frame, text="Back", command=self.manage_account_screen(self.current_account_id)).grid(row=len(transactions) + 1, column=0, pady=10)

    def create_account_screen(self):
        username = simpledialog.askstring("Create Account", "Enter username:")
        password = simpledialog.askstring("Create Account", "Enter password:", show='*')
        if username and password:
            success = self.user_account.create_account(username, password)
            if success:
                messagebox.showinfo("Success", "Account created successfully")
            else:
                messagebox.showerror("Error", "Username already exists")
        self.show_login_screen()

    def create_bank_account_screen(self):
        account_type = simpledialog.askstring("Account Type", "Enter account type (Checking/Savings):")
        if account_type:
            BankAccount(self.user_account.get_current_user_id()).create_account(account_type.capitalize())
            messagebox.showinfo("Success", f"{account_type.capitalize()} account created successfully")
        self.show_main_screen()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.user_account.login(username, password):
            self.show_main_screen()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def logout(self):
        self.user_account.logout()
        self.show_login_screen()

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BankApp(root)
    root.mainloop()

    conn.close()
