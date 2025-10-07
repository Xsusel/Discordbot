package com.launcher;

import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.ComboBox;
import javafx.scene.control.Label;
import javafx.scene.control.ListView;
import javafx.scene.control.ProgressBar;
import javafx.scene.control.TextField;

public class LauncherController {

    @FXML
    private TextField usernameField;

    @FXML
    private ComboBox<String> versionComboBox;

    @FXML
    private Button launchButton;

    @FXML
    private TextField searchField;

    @FXML
    private Button searchButton;

    @FXML
    private ListView<String> modpackListView;

    @FXML
    private Button installButton;

    @FXML
    private Button updateButton;

    @FXML
    private ProgressBar progressBar;

    @FXML
    private Label statusLabel;

    @FXML
    public void initialize() {
        // This method is called after the FXML file has been loaded.
        // We will populate the version combo box and set up initial state here.
        statusLabel.setText("Launcher is ready.");
    }

    @FXML
    private void launchGame() {
        System.out.println("Launch button clicked!");
        // Logic for launching the game will go here.
    }

    @FXML
    private void searchForModpacks() {
        System.out.println("Search button clicked!");
        // Logic for searching for modpacks will go here.
    }

    @FXML
    private void installModpack() {
        System.out.println("Install button clicked!");
        // Logic for installing the selected modpack will go here.
    }

    @FXML
    private void checkForUpdates() {
        System.out.println("Check for Updates button clicked!");
        // Logic for checking for updates will go here.
    }
}