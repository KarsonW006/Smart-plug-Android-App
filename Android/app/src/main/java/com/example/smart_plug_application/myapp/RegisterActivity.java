package com.example.smart_plug_application.myapp;

import android.os.Bundle;
import android.util.Log;
import android.util.Patterns;
import android.view.View;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import okhttp3.ResponseBody;
import org.json.JSONObject;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import com.example.smart_plug_application.R;
import com.google.gson.Gson;
import android.content.Intent;

public class RegisterActivity extends AppCompatActivity {

    // Define variables for UI elements and error message
    private EditText etUserID;
    private EditText etUserName;
    private EditText etTapoPassword;
    private EditText etPassword;
    private EditText etConfirmPassword;
	private String errmessage = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);

        //Initialize UI elements
        etUserID = findViewById(R.id.etUserID);
        etUserName = findViewById(R.id.etUserName);
        etTapoPassword = findViewById(R.id.etTapoPassword);
        etPassword = findViewById(R.id.etPassword);
        etConfirmPassword = findViewById(R.id.etConfirmPassword);

        // Set hint for User ID field dynamically
        etUserID.setHint("Enter your Tapo ID as User ID");

	// Set onClickListener for the register button to add new user record
        findViewById(R.id.btnRegister).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                registerUser();
            }
        });

        // Set up Cancel button to return to LoginActivity
        findViewById(R.id.btnCancel).setOnClickListener(view -> {
            Intent intent = new Intent(RegisterActivity.this, LoginActivity.class);
            startActivity(intent);
            finish(); // Close RegisterActivity
        });

    }

    // Function to validate email format
    public boolean isValidEmail(String email) {
        return Patterns.EMAIL_ADDRESS.matcher(email).matches();
    }

    // Function to validate new password, password must be 8-15 characters long, include upper/lower case, numeric, and special characters.
    public boolean isValidPassword(String password) {
        // Check password length
        if (password.length() < 8 || password.length() > 15) {
            errmessage = "Password must be 8-15 characters long";
            return false;
        }

        // Check for at least one upper case letter
        if (!password.matches(".*[A-Z].*")) {
            errmessage = "Password must include uppercase";
            return false;
        }

        // Check for at least one lower case letter
        if (!password.matches(".*[a-z].*")) {
            errmessage = "Password must include lowercase";
            return false;
        }

        // Check for at least one numeric character
        if (!password.matches(".*[0-9].*")) {
            errmessage = "Password must include numeric";
            return false;
        }

        // Check for at least one special character
        if (!password.matches(".*[~`!@#$%^&*()\\-_=+\\[{\\]}\\\\|;:'\"<>,. ?].*")) {
            errmessage = "Password must include special characters";
            return false;
        }
        return true;
    }

    public String getErrorMessage() {
        return errmessage;
    }

    // Process registration : Check Password must equal Confirm Password before connect and insert user record
    private void registerUser() {
        String userID = etUserID.getText().toString();
        String userName = etUserName.getText().toString();
        String tapoPassword = etTapoPassword.getText().toString();
        String password = etPassword.getText().toString();
        String confirmPassword = etConfirmPassword.getText().toString();

        if (userID.isEmpty() || userName.isEmpty() || tapoPassword.isEmpty() || password.isEmpty() || confirmPassword.isEmpty()) {
            Toast.makeText(this, "Please fill in all fields", Toast.LENGTH_SHORT).show();
            return;
        }

        // Check if passwords match
        if (!password.equals(confirmPassword)) {
            Toast.makeText(this, "Passwords and Confirm Password do not match", Toast.LENGTH_SHORT).show();
            return;
        }

        // Validate email format
        if (!isValidEmail(userID)) {
            Toast.makeText(this, "Please enter a valid email address", Toast.LENGTH_SHORT).show();
            return;
        }

        // Validate password
        if (!isValidPassword(password)) {
		Toast.makeText(this, errmessage , Toast.LENGTH_LONG).show();
            return;
        }

        //Setup and send POST request to Node JS to update database for new user record
        // Call the API for registration
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
        User user = new User(userID, userName, tapoPassword, password);
        Call<ResponseBody> call = apiService.registerUser(user);

       // Log.d("RegisterActivity", "Request Body: " + new Gson().toJson(user));

	// Handle the API response
        call.enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call, Response<ResponseBody> response) {
                try {
                    if (response.isSuccessful() && response.body() != null) {
                        String jsonResponse = response.body().string();
                       // Log.d("RegisterResponse", jsonResponse);

                        //Check the return message for display the result
                        JSONObject jsonObject = new JSONObject(jsonResponse);
                        String message = jsonObject.optString("message");

			// If registration is successful
                        if ("User registered successfully".equals(message)) {
                            Toast.makeText(RegisterActivity.this, "User registration successful", Toast.LENGTH_SHORT).show();
                            finish();
                        } else {
                            Toast.makeText(RegisterActivity.this, "Registration Failed: " + message, Toast.LENGTH_SHORT).show();
                        }
                    } else {
                        //Check the return message for not successful case
                        String errorBody = response.errorBody().string();
                        //Log.d("RegisterError", errorBody);
                        JSONObject errorObject = new JSONObject(errorBody);
                        String errorMessage = errorObject.optString("error");
                        Toast.makeText(RegisterActivity.this, "Registration Failed: " + errorMessage, Toast.LENGTH_SHORT).show();
                    }
                } catch (Exception e) {
                    //Forced exception handling to prevent cause the program to crash
                    e.printStackTrace();
                    Toast.makeText(RegisterActivity.this, "Registration Failed: Error parsing response", Toast.LENGTH_SHORT).show();
                }
            }

            // Handle on failure case
            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                Toast.makeText(RegisterActivity.this, "An error occurred: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}
