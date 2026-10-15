package com.example.smart_plug_application.ui.settings;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;

import com.example.smart_plug_application.R;
import com.example.smart_plug_application.databinding.FragmentSettingsBinding;
import com.example.smart_plug_application.myapp.ChangePassword;
import com.example.smart_plug_application.myapp.LoginActivity;
import com.example.smart_plug_application.myapp.ApiClient;
import com.example.smart_plug_application.myapp.ApiService;
import com.example.smart_plug_application.myapp.Notification;
import com.example.smart_plug_application.myapp.NotificationSetting;
import com.example.smart_plug_application.myapp.RegisterActivity;

import com.google.android.material.switchmaterial.SwitchMaterial;

import java.util.List;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class SettingsFragment extends Fragment {

    // Define variables for UI elements and shared preferences
    private static final String TAG = "SettingsFragment";
    private FragmentSettingsBinding binding;
    private Button btnLogout;
    private EditText etOldPassword, etNewPassword, etConfirmNewPassword;
    private Button btnSavePassword;
    private SwitchMaterial switchNotification;
    private SharedPreferences sharedPreferences;
    private ApiService apiService;

    // Initialize apiService and sharedPreferences
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        apiService = ApiClient.getApiService();
        sharedPreferences = getActivity().getSharedPreferences("MyAppPrefs", getActivity().MODE_PRIVATE);
    }
    // Inflates UI, binds views, sets up listeners
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        View root = inflater.inflate(R.layout.fragment_settings, container, false);

        // Initialize UI elements
        etOldPassword = root.findViewById(R.id.et_old_password);
        etNewPassword = root.findViewById(R.id.et_new_password);
        etConfirmNewPassword = root.findViewById(R.id.et_confirm_new_password);
        btnSavePassword = root.findViewById(R.id.btn_save_password);
        switchNotification = root.findViewById(R.id.switch_notification);
        btnLogout = root.findViewById(R.id.btn_logout);

        sharedPreferences = getActivity().getSharedPreferences("MyAppPrefs", getActivity().MODE_PRIVATE);

        // Set up the Save Password button click listener
        btnSavePassword.setOnClickListener(v -> handleChangePassword());

        // Set up the Notification switch toggle listener
        switchNotification.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (switchNotification.isPressed()) {
                handleToggleNotification(isChecked);
            }
        });
	//Log.d(TAG, "Switch toggled by user: " + isChecked);
        // Retrieve the current notification setting
        retrieveNotificationSetting();

        // Set up the Logout button click listener
        btnLogout.setOnClickListener(v -> logout());

        return root;
    }

    // Retrieve the notification setting when the fragment resumes
    @Override
    public void onResume() {
        super.onResume();
        retrieveNotificationSetting();
    }

    // Validates password inputs and calls API to change password
    private void handleChangePassword() {
        String oldPassword = etOldPassword.getText().toString();
        String newPassword = etNewPassword.getText().toString();
        String confirmNewPassword = etConfirmNewPassword.getText().toString();

        // Check if any password field is empty
        if (newPassword.isEmpty() || confirmNewPassword.isEmpty()|| oldPassword.isEmpty()) {
            Toast.makeText(getActivity(), "Old Password or New Password or Confirm New Password is empty", Toast.LENGTH_SHORT).show();
            return;
        }

        // Check if new password and confirm password match
        if (!newPassword.equals(confirmNewPassword)) {
            Toast.makeText(getActivity(), "New Password and Confirm New Password do not match", Toast.LENGTH_SHORT).show();
            return;
        }

        RegisterActivity registerActivity = new RegisterActivity();

        // Validate password complexity, password must be 8-15 characters long, include upper/lower case, numeric, and special characters.
        if (!registerActivity.isValidPassword(newPassword)) {
            //Toast.makeText(getActivity(), "Password must be 8-15 characters long, include upper/lower case, numeric, and special characters.", Toast.LENGTH_SHORT).show();
            Toast.makeText(getActivity(), registerActivity .getErrorMessage() , Toast.LENGTH_SHORT).show();
            return;
        }

        String userid = sharedPreferences.getString("userid", "");

        // Create a ChangePassword object for Change Password
        ChangePassword changepassword = new ChangePassword(userid, oldPassword, newPassword);

        // Call the Change Password API
        Call<ResponseBody> call = apiService.changePassword(changepassword);

        call.enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call, Response<ResponseBody> response) {
                if (response.isSuccessful()) {
                    // Show success message and reset input fields
                    Toast.makeText(getActivity(), "Password changed successfully", Toast.LENGTH_SHORT).show();
                    etOldPassword.setText("");
                    etNewPassword.setText("");
                    etConfirmNewPassword.setText("");
                } else {
                    Toast.makeText(getActivity(), "Failed to change password", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                Log.e(TAG, "API call failed: " + t.getMessage());
                Toast.makeText(getActivity(), "Failed to change password", Toast.LENGTH_SHORT).show();
            }
        });
    }

    // Update the notification setting via the API
    private void handleToggleNotification(boolean isChecked) {
        String userid = sharedPreferences.getString("userid", "");
        String notify = isChecked ? "Y" : "N";

        // Create a notification object for Change Password
        Notification notification = new Notification(userid, notify);

        // Call the update notification API
        Call<ResponseBody> call = apiService.updateNotificationSetting(notification);

        call.enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call, Response<ResponseBody> response) {
                if (response.isSuccessful()) {
                    Toast.makeText(getActivity(), "Notification setting updated successfully", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(getActivity(), "Failed to update notification setting", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                Log.e(TAG, "API call failed: " + t.getMessage());
                Toast.makeText(getActivity(), "Failed to update notification setting", Toast.LENGTH_SHORT).show();
            }
        });
    }

    // Retrieve the current notification setting from the server
    private void retrieveNotificationSetting() {
        String userid = sharedPreferences.getString("userid", "");
        //Log.d(TAG, "Retrieving notification setting for userid: " + userid);
        apiService.retrieveNotificationSetting(userid).enqueue(new Callback<List<NotificationSetting>>() {
            @Override
            public void onResponse(@NonNull Call<List<NotificationSetting>> call, @NonNull Response<List<NotificationSetting>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    // Get the response result and display the value
                    List<NotificationSetting> settings = response.body();
                    if (!settings.isEmpty()) {
                        String notify = settings.get(0).getNotify();

                        switchNotification.setChecked("Y".equals(notify));

                    } else {
                        Log.e(TAG, "Notification setting list is empty");
                    }
                } else {
                    Log.e(TAG, "Failed to retrieve notification setting: " + response.message());
                    Toast.makeText(getActivity(), "Failed to retrieve notification setting", Toast.LENGTH_SHORT).show();
                }
            }

            // handle on failure case
            @Override
            public void onFailure(@NonNull Call<List<NotificationSetting>> call, @NonNull Throwable t) {
                Log.e(TAG, "API call failed: " + t.getMessage());
                Toast.makeText(getActivity(), "Failed to retrieve notification setting", Toast.LENGTH_SHORT).show();
            }
        });
    }

	// Clear binding when the view is destroyed
    @Override
    public void onDestroyView() {
        super.onDestroyView();
    }

    // Log out the user by clearing the session and navigating to the login screen
    private void logout() {
        // Clear SharedPreferences
        SharedPreferences.Editor editor = sharedPreferences.edit();
        editor.clear();
        editor.apply();

        // Start LoginActivity
        Intent intent = new Intent(getActivity(), LoginActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);

        // Close the current activity
        getActivity().finishAffinity();
    }
}
