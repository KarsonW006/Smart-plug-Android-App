package com.example.smart_plug_application.ui.home;

import android.os.Bundle;

import androidx.fragment.app.Fragment;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import com.example.smart_plug_application.R;
import android.graphics.Color;
import android.util.Log;
import android.widget.Toast;

import com.example.smart_plug_application.myapp.ApiClient;

import com.example.smart_plug_application.myapp.ForecastData;
import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;

import java.text.ParseException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import com.github.mikephil.charting.components.AxisBase;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.components.YAxis;
import com.github.mikephil.charting.data.Entry;

import com.github.mikephil.charting.formatter.ValueFormatter;

import java.text.SimpleDateFormat;
import java.util.Locale;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;


public class AnalyticalInfoFragment extends Fragment {

    // Define variables
    private LineChart lineChartMonthly;
    private LineChart lineChartQuarterly;

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        View view = inflater.inflate(R.layout.fragment_analytical_info, container, false);

        //Initialize UI elements
        lineChartMonthly = view.findViewById(R.id.lineChartMonthly);
        lineChartQuarterly = view.findViewById(R.id.lineChartQuarterly);

        fetchData();
        return view;
    }

    // Call API to fetch data
    private void fetchData() {
        ApiClient.getApiService().getForecastedPrices().enqueue(new Callback<List<ForecastData>>() {
            @Override
            public void onResponse(Call<List<ForecastData>> call, Response<List<ForecastData>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<ForecastData> forecastDataList = response.body();
                    populateCharts(forecastDataList);
                }
            }

            // handle on failure case
            @Override
            public void onFailure(Call<List<ForecastData>> call, Throwable t) {
                Toast.makeText(getContext(), "Failed to load data", Toast.LENGTH_SHORT).show();
            }
        });
    }

    // Populate the monthly ans quarterly charts
    private void populateCharts(List<ForecastData> forecastDataList) {
        // Define arrays
        List<Entry> monthlyPrices = new ArrayList<>();
        List<Entry> monthlyLower = new ArrayList<>();
        List<Entry> monthlyUpper = new ArrayList<>();

        List<Entry> quarterlyPrices = new ArrayList<>();
        List<Entry> quarterlyLower = new ArrayList<>();
        List<Entry> quarterlyUpper = new ArrayList<>();

        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.getDefault());

        for (ForecastData data : forecastDataList) {
            try {
                long timestamp = dateFormat.parse(data.forecast_date).getTime(); // Convert to timestamp
                //Log.d("TimestampDebug", "Forecast Date: " + data.forecast_date + ", Timestamp: " + timestamp);
                // Assign value to the arrays
                if ("monthly".equals(data.forecast_type)) {
                    monthlyPrices.add(new Entry(timestamp, (float) data.forecast_price));
                    monthlyLower.add(new Entry(timestamp, (float) data.forecast_price_lower));
                    monthlyUpper.add(new Entry(timestamp, (float) data.forecast_price_upper));
                } else if ("quarterly".equals(data.forecast_type)) {
                    quarterlyPrices.add(new Entry(timestamp, (float) data.forecast_price));
                    quarterlyLower.add(new Entry(timestamp, (float) data.forecast_price_lower));
                    quarterlyUpper.add(new Entry(timestamp, (float) data.forecast_price_upper));
                }
            } catch (ParseException e) {
                //Forced exception handling to prevent cause the program to crash
                e.printStackTrace(); // Handle parsing error
                Log.e("TimestampError", "Error parsing date: " + data.forecast_date);
            }
        }
        // call function to setup the charts
        setupChart(lineChartMonthly, monthlyPrices, monthlyLower, monthlyUpper, "Monthly Price Forecast");
        setupChart(lineChartQuarterly, quarterlyPrices, quarterlyLower, quarterlyUpper, "Quarterly Price Forecast");
    }

    // Setup the charts
    private void setupChart(LineChart lineChart, List<Entry> priceData, List<Entry> lowerData, List<Entry> upperData, String title) {
        LineDataSet priceSet = new LineDataSet(priceData, "Forecast Price");
        priceSet.setColor(Color.BLUE);
        priceSet.setValueTextSize(0f);
        //priceSet.setLineWidth(2f);
        priceSet.setDrawValues(false);
        priceSet.setDrawCircles(false);

        LineDataSet lowerSet = new LineDataSet(lowerData, "Lower Price");
        lowerSet.setColor(Color.RED);
        lowerSet.setValueTextSize(0f);
        lowerSet.setDrawValues(false);
        lowerSet.setDrawCircles(false);
        //lowerSet.setLineWidth(2f);
        lowerSet.enableDashedLine(10f, 10f, 0f);

        LineDataSet upperSet = new LineDataSet(upperData, "Upper Price");
        upperSet.setColor(Color.GREEN);
        upperSet.setValueTextSize(0f);
        upperSet.setDrawValues(false);
        upperSet.setDrawCircles(false);
       //upperSet.setLineWidth(2f);
        upperSet.enableDashedLine(10f, 10f, 0f);

        LineData lineData = new LineData(priceSet, lowerSet, upperSet);
        lineChart.setData(lineData);

        // Set the description as the chart title
        lineChart.getDescription().setText(title);

        // Set up X-axis
        XAxis xAxis = lineChart.getXAxis();
        xAxis.setValueFormatter(new YearValueFormatter());
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM); // Labels at the bottom
        xAxis.setGranularity(1f); // Ensure only 1-year intervals are displayed
        xAxis.setLabelCount(5); // Adjust the label count as needed
        xAxis.setDrawLabels(true);
        xAxis.setGranularity(1); // Set interval
        xAxis.setGranularityEnabled(true);
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);

        // Set up Y-axis
        YAxis leftAxis = lineChart.getAxisLeft();
        leftAxis.setGranularity(5f); // Y-axis interval
        leftAxis.setAxisMinimum(-5f); // Minimum value
        //leftAxis.setLabelCount(5, true); // Y-axis label count

        // Disable the right Y-axis
        YAxis rightAxis = lineChart.getAxisRight();
        rightAxis.setEnabled(false);

        lineChart.getLegend().setEnabled(true);
        lineChart.invalidate(); // Refresh the chart

    }

    // Custom formatter for X-axis labels only show year instead of month
    public class YearValueFormatter extends ValueFormatter {
        private final SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy", Locale.getDefault());

        @Override
        public String getAxisLabel(float value, AxisBase axis) {
            // value is already a timestamp in milliseconds
            Date date = new Date((long) value);
            return dateFormat.format(date);
        }

    }

}

