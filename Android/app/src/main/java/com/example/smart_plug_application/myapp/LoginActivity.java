package com.example.smart_plug_application.myapp;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import okhttp3.ResponseBody;
import org.json.JSONObject;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import com.example.smart_plug_application.R;
import com.example.smart_plug_application.MainActivity;
import android.widget.Button;

public class LoginActivity extends AppCompatActivity {
    // Define variables for UI elements and API service
    private EditText userIdField, passwordField;
    private Button btnLogin, btnRegister;
    private ApiService apiService;
    private EditText etUserID;
    private EditText etPassword;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        //Initialize UI elements
        etUserID = findViewById(R.id.etUserID);
        etPassword = findViewById(R.id.etPassword);
        btnLogin = findViewById(R.id.btnLogin);
        btnRegister = findViewById(R.id.btnRegister);

	// Initialize ApiService instance
        apiService = ApiClient.getRetrofitInstance().create(ApiService.class);

	// Set onClickListener for the login button to handle login
        btnLogin.setOnClickListener(view -> handleLogin());

	// Set onClickListener for the register button to navigate to RegisterActivity
        btnRegister.setOnClickListener(view -> {
            Intent intent = new Intent(LoginActivity.this, RegisterActivity.class);
            startActivity(intent);
        });
    }

    // Method to handle login logic
    private void handleLogin() {
        String userID = etUserID.getText().toString();
        String password = etPassword.getText().toString();

        // Validate that User ID and Password fields are not empty
        if (userID.isEmpty() || password.isEmpty()) {
            Toast.makeText(this, "User ID and password cannot be empty", Toast.LENGTH_SHORT).show();
            return;
        }

        // Create a UserLogin object with user credentials
        UserLogin userLogin = new UserLogin(userID, password);

	// Call the login API
        Call<ResponseBody> call = apiService.loginUser(userLogin);

	// Enqueue the API call to run asynchronously
        call.enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call, Response<ResponseBody> response) {
                if (response.isSuccessful()) {
                    try {
			// Parse the JSON response
                        String jsonResponse = response.body().string();
                        //Log.d("LoginResponse", jsonResponse);
                        // Receive Response result and assign value
                        JSONObject jsonObject = new JSONObject(jsonResponse);
                        String token = jsonObject.optString("token");
                        String userName = jsonObject.optString("userName");

                        if (!token.isEmpty()) {
                            // Save the user ID and user name in SharedPreferences
                            SharedPreferences sharedPreferences = getSharedPreferences("MyAppPrefs", MODE_PRIVATE);
                            SharedPreferences.Editor editor = sharedPreferences.edit();
                            editor.putString("username", userName);
                            editor.putString("userid", userID);
                            editor.apply();

                            // Display login successful message and navigate to MainActivity
                            Toast.makeText(LoginActivity.this, "Login Successful", Toast.LENGTH_SHORT).show();
                            startActivity(new Intent(LoginActivity.this, MainActivity.class));
                            finish();
                        } else {
                            Toast.makeText(LoginActivity.this, "Login Failed: Invalid token", Toast.LENGTH_SHORT).show();
                        }
                    } catch (Exception e) {
                        //Handle JSON parsing errors
                        e.printStackTrace();
                        Toast.makeText(LoginActivity.this, "Login Failed: Error parsing response", Toast.LENGTH_SHORT).show();
                    }
                } else {
                    // Handle unsuccessful response
                    try {
                        String errorBody = response.errorBody().string();
                        Log.d("LoginError", errorBody);
                        JSONObject errorObject = new JSONObject(errorBody);
                        String errorMessage = errorObject.optString("error");
                        Toast.makeText(LoginActivity.this, "Login Failed: " + errorMessage, Toast.LENGTH_SHORT).show();
                    } catch (Exception e) {
                        //Handle errors while parsing error response
                        e.printStackTrace();
                        Toast.makeText(LoginActivity.this, "Login Failed: " + response.message(), Toast.LENGTH_SHORT).show();
                    }
                }
            }

            // Handle failure scenario for API call
            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                Toast.makeText(LoginActivity.this, "An error occurred: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}
