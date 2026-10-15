package com.example.smart_plug_application.myapp;

import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;
// Base URL for the API
public class ApiClient {
    private static final String BASE_URL = "https://example.com/"; // Placeholder: configure your own API URL if restoring the backend
	// Retrofit instance
    private static Retrofit retrofit;

    /**
     * Method to get the Retrofit instance.
     * Creates a new instance if it doesn't already exist.
     *
     * @return Retrofit instance
     */
    public static Retrofit getRetrofitInstance() {
	// Check if the retrofit instance is null
        if (retrofit == null) {
            // Avoid logging request/response bodies because they may contain passwords or tokens.
            retrofit = new Retrofit.Builder()
                    .baseUrl(BASE_URL)
                    .addConverterFactory(GsonConverterFactory.create())
                    .build();
        }

        return retrofit;
    }

    /**
     * Method to get the ApiService instance.
     * Uses the Retrofit instance to create the ApiService.
     *
     * @return ApiService instance
     */
    public static ApiService getApiService() {
        return getRetrofitInstance().create(ApiService.class);
    }

}