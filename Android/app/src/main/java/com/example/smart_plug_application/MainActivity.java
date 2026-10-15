package com.example.smart_plug_application;

import android.os.Bundle;

import com.google.android.material.bottomnavigation.BottomNavigationView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.navigation.NavController;
import androidx.navigation.Navigation;
import androidx.navigation.ui.AppBarConfiguration;
import androidx.navigation.ui.NavigationUI;

import androidx.navigation.fragment.NavHostFragment;
import com.example.smart_plug_application.R;

import com.example.smart_plug_application.databinding.ActivityMainBinding;

public class MainActivity extends AppCompatActivity {
	// Declare a variable for view binding
    private ActivityMainBinding binding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

	// Initialize view binding
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

	// Initialize the BottomNavigationView
        BottomNavigationView navView = findViewById(R.id.nav_view);

	// Define the top-level destinations for the navigation
        AppBarConfiguration appBarConfiguration = new AppBarConfiguration.Builder(
                R.id.navigation_home, R.id.navigation_dashboard, R.id.navigation_settings)
                .build();

	// Get the NavController for the navigation host fragment
        NavController navController = Navigation.findNavController(this, R.id.nav_host_fragment_activity_main);

	// Set up the ActionBar with the NavController and the AppBarConfiguration
        NavigationUI.setupActionBarWithNavController(this, navController, appBarConfiguration);

	// Set up the BottomNavigationView with the NavController
        NavigationUI.setupWithNavController(binding.navView, navController);
    }

    @Override
    public boolean onSupportNavigateUp() {
        // Ensure the "Up" button works with NavController
        NavHostFragment navHostFragment =
                (NavHostFragment) getSupportFragmentManager().findFragmentById(R.id.nav_host_fragment_activity_main);
        NavController navController = navHostFragment.getNavController();

	// Handle navigation when the "Up" button is pressed
        return navController.navigateUp() || super.onSupportNavigateUp();
    }
}