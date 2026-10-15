package com.example.smart_plug_application.ui.home;

import android.graphics.Color;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.example.smart_plug_application.myapp.ApiClient;
import com.example.smart_plug_application.myapp.ApiService;
import com.example.smart_plug_application.myapp.PriceData;
import com.example.smart_plug_application.myapp.PricingDetailsAdapter;
import com.example.smart_plug_application.R;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import java.util.Locale;
import java.util.Date;


public class PricingDetailsFragment extends Fragment {

    // Define variables for UI elements, RecyclerView adapter and data
    private Button btnToday, btnTomorrow;
    private RecyclerView recyclerViewPricingDetails;
    private TextView noDataMessage;
    private PricingDetailsAdapter adapter;
    private List<PriceData> priceDataList = new ArrayList<>();
    private String selectedDate;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        View view = inflater.inflate(R.layout.fragment_pricingdetails, container, false);

        // Initialize UI elements
        btnToday = view.findViewById(R.id.btnToday);
        btnTomorrow = view.findViewById(R.id.btnTomorrow);
        recyclerViewPricingDetails = view.findViewById(R.id.recyclerViewPricingDetails);
        noDataMessage = view.findViewById(R.id.noDataMessage);

        // RecyclerView setup
        recyclerViewPricingDetails.setLayoutManager(new LinearLayoutManager(getContext()));
        adapter = new PricingDetailsAdapter(priceDataList);
        recyclerViewPricingDetails.setAdapter(adapter);

        // Set up button click listeners
        btnToday.setOnClickListener(v -> loadPricingData("today"));
        btnTomorrow.setOnClickListener(v -> loadPricingData("tomorrow"));

        // Load today's data by default
        loadPricingData("today");

        return view;
    }

    // Method to load pricing data based on the selected day
    private void loadPricingData(String day) {
        // Adjust button styles
        if (day.equals("today")) {
            selectedDate = getTodayDate();
            setButtonStyles(btnToday, btnTomorrow);
        } else {
            selectedDate = getTomorrowDate();
            setButtonStyles(btnTomorrow, btnToday);
        }

        // Create an instance of the API service
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);

	// Call the API to get price data
        Call<List<PriceData>> call = apiService.getPriceData();

	// Enqueue the call to be executed asynchronously
        call.enqueue(new Callback<List<PriceData>>() {
            @Override
            public void onResponse(Call<List<PriceData>> call, Response<List<PriceData>> response) {
		// If the response is successful and not null, filter and display the data
                if (response.isSuccessful() && response.body() != null) {
                    // Call function to filter the price data and display
                    filterAndDisplayData(response.body());
                } else {
                    // Show no data message if response is not successful
                    showNoDataMessage();
                }
            }

            // handle on failure case
            @Override
            public void onFailure(Call<List<PriceData>> call, Throwable t) {
		// Show no data message if no data matches the selected date
                showNoDataMessage();
            }
        });
    }

    // Method to filter and display the data based on the selected date
    private void filterAndDisplayData(List<PriceData> data) {
        List<PriceData> filteredData = new ArrayList<>();
        for (PriceData item : data) {
		// Add items to filteredData if they match the selected date
            if (item.getValidFromDate().equals(selectedDate)) {
                filteredData.add(item);
            }
        }

        if (filteredData.isEmpty()) {
		// Show no data message if no data matches the selected date
            showNoDataMessage();
        } else {
            // Clear and re-assign the price list for price table display.
            priceDataList.clear();		
            priceDataList.addAll(filteredData);   // Update the list with filtered data
            adapter.notifyDataSetChanged();    // Notify the adapter of data changes
            recyclerViewPricingDetails.setVisibility(View.VISIBLE);   // Show the RecyclerView
            noDataMessage.setVisibility(View.GONE);   // Hide the no data message
        }
    }

    // Display no data message
    private void showNoDataMessage() {
        recyclerViewPricingDetails.setVisibility(View.GONE);   // Hide the RecyclerView
        noDataMessage.setVisibility(View.VISIBLE);   // Show the no data message
    }

    // Adjust the button styles base on the select button (today / Tomorrow)
    private void setButtonStyles(Button selected, Button unselected) {
        selected.setBackgroundColor(ContextCompat.getColor(getContext(), R.color.buttonColor));
        selected.setTextColor(ContextCompat.getColor(getContext(), R.color.white));

        unselected.setBackgroundColor(ContextCompat.getColor(getContext(), R.color.white));
        unselected.setTextColor(ContextCompat.getColor(getContext(), R.color.buttonColor));
        unselected.setBackgroundResource(R.drawable.button_outline); // Create an outline drawable
    }

    // Method to get today's date in the format yyyy-MM-dd
    private String getTodayDate() {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(new Date());
    }

    // Method to get tomorrow's date in the format yyyy-MM-dd
    private String getTomorrowDate() {
        Calendar calendar = Calendar.getInstance();
        calendar.add(Calendar.DAY_OF_YEAR, 1);   // Add one day to the current date
        return new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(calendar.getTime());
    }
}

