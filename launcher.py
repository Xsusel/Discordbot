import tkinter as tk
from tkinter import ttk, messagebox
import threading
from curseforge_api import CurseForgeAPI, API_KEY
from minecraft_manager import MinecraftManager

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Minecraft Launcher")
        self.geometry("800x600")

        self.cf_api = CurseForgeAPI(API_KEY)
        self.mc_manager = MinecraftManager(self.cf_api)

        # Username
        self.username_label = ttk.Label(self, text="Username:")
        self.username_label.pack()
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack()

        # Minecraft Version
        self.version_label = ttk.Label(self, text="Minecraft Version:")
        self.version_label.pack()
        self.version_combobox = ttk.Combobox(self, state="readonly")
        self.version_combobox.pack()
        self.load_minecraft_versions()

        # Launch Button
        self.launch_button = ttk.Button(self, text="Launch Minecraft", command=self.launch_game_action)
        self.launch_button.pack()

    def launch_game_action(self):
        username = self.username_entry.get()
        version = self.version_combobox.get()
        if not username:
            messagebox.showerror("Error", "Please enter a username.")
            return
        if not version:
            messagebox.showerror("Error", "Please select a Minecraft version.")
            return

        self.launch_button.config(state=tk.DISABLED)
        self.update_status(f"Launching Minecraft {version}...")

        thread = threading.Thread(target=self._launch_game_thread, args=(username, version))
        thread.start()

    def _launch_game_thread(self, username, version):
        self.mc_manager.launch_game(username, version)
        self.after(0, self.on_launch_complete)

    def on_launch_complete(self):
        self.launch_button.config(state=tk.NORMAL)
        self.update_status("Ready")

    def load_minecraft_versions(self):
        try:
            versions = self.cf_api.get_minecraft_versions()
            self.version_combobox['values'] = [v['versionString'] for v in versions]
            if self.version_combobox['values']:
                self.version_combobox.current(0)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load Minecraft versions: {e}")

        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill='x', pady=10)

        # CurseForge Search
        self.search_label = ttk.Label(self, text="Search for Modpacks on CurseForge:")
        self.search_label.pack()
        self.search_entry = ttk.Entry(self)
        self.search_entry.pack()
        self.search_button = ttk.Button(self, text="Search", command=self.search_for_modpacks)
        self.search_button.pack()

        # Modpack List
        self.modpacks = {} # To store the full modpack data
        self.modpack_listbox = tk.Listbox(self, width=50)
        self.modpack_listbox.pack()

        # Install Modpack Button
        self.install_button = ttk.Button(self, text="Install Modpack", command=self.install_modpack_action)
        self.install_button.pack()

        # Update Button
        self.update_button = ttk.Button(self, text="Check for Updates", command=self.check_for_updates_action)
        self.update_button.pack()

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        self.status_var.set(message)
        self.update_idletasks()

    def update_progress(self, progress):
        # This is called from a worker thread, so we schedule the UI update
        self.after(0, lambda: self.progress_bar.config(value=progress))

    def reset_progress(self):
        self.after(0, lambda: self.progress_bar.config(value=0))

    def check_for_updates_action(self):
        self.update_status("Checking for updates...")
        updated, message, modpack_data = self.mc_manager.check_for_updates()
        self.update_status("Ready")

        if updated is None:
            messagebox.showerror("Update Check", message)
        elif updated:
            if messagebox.askyesno("Update Available", f"{message}\nDo you want to install it now?"):
                self.install_button.config(state=tk.DISABLED)
                self.update_status(f"Updating {modpack_data['name']}...")
                thread = threading.Thread(target=self._install_modpack_thread, args=(modpack_data,))
                thread.start()
        else:
            messagebox.showinfo("Update Check", message)

    def install_modpack_action(self):
        selected_indices = self.modpack_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a modpack to install.")
            return

        selected_modpack_name = self.modpack_listbox.get(selected_indices[0])
        modpack_data = self.modpacks.get(selected_modpack_name)

        if not modpack_data:
            messagebox.showerror("Error", "Could not find data for the selected modpack.")
            return

        self.install_button.config(state=tk.DISABLED)
        self.update_status(f"Installing {selected_modpack_name}...")

        thread = threading.Thread(target=self._install_modpack_thread, args=(modpack_data,))
        thread.start()

    def _install_modpack_thread(self, modpack_data):
        self.mc_manager.install_modpack(modpack_data, self.update_progress, self.update_status)
        self.after(0, self.on_install_complete)

    def on_install_complete(self):
        self.install_button.config(state=tk.NORMAL)
        self.reset_progress()
        # The final status is set by the manager, so we can just set it to Ready here.
        self.update_status("Ready.")

    def search_for_modpacks(self):
        query = self.search_entry.get()
        version = self.version_combobox.get()
        if not query:
            messagebox.showinfo("Search", "Please enter a search query.")
            return

        try:
            modpacks = self.cf_api.search_modpacks(query, game_version=version)
            self.modpack_listbox.delete(0, tk.END)
            self.modpacks.clear()
            for modpack in modpacks:
                self.modpack_listbox.insert(tk.END, modpack['name'])
                self.modpacks[modpack['name']] = modpack
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search for modpacks: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()