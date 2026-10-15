package com.example.smart_plug_application.ui.home;

import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.navigation.fragment.NavHostFragment;

import com.example.smart_plug_application.R;
import com.example.smart_plug_application.myapp.ApiClient;
import com.example.smart_plug_application.myapp.ApiService;
import com.example.smart_plug_application.myapp.HighHour;
import com.example.smart_plug_application.myapp.PriceData;
import com.example.smart_plug_application.myapp.ThresholdData;
import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.AxisBase;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.components.YAxis;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;
import com.github.mikephil.charting.formatter.ValueFormatter;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

import java.text.ParseException;
import java.util.Date;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;

import com.github.mikephil.charting.highlight.Highlight;
import com.github.mikephil.charting.interfaces.dataprovider.LineDataProvider;
import com.github.mikephil.charting.renderer.LineChartRenderer;
import com.github.mikephil.charting.utils.Transformer;
import com.github.mikephil.charting.utils.ViewPortHandler;


public class HomeFragment extends Fragment {

     // Define variables for UI elements and data
    private LineChart stepChart;
    private Button btnToday, btnTomorrow, btnViewMore, btnAnalyticalInfo;
    private TextView tvHighPrice, tvLowPrice, tvAvgPrice, noDataText, tvDailyPricingInfoTitle;
    private TextView tvThresholdHighPrice, tvThresholdLowPrice, tvHighRatesHours;
    private List<PriceData> todayData, tomorrowData;
    private Integer lowestPrice = 0;
    private Handler handler;
    private Runnable runnable;
    private static final long INTERVAL = 60000; // 1 minute
    private boolean isToday; // Th is a flag for setting the Custom LineChart Renderer

    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        View root = inflater.inflate(R.layout.fragment_home, container, false);

        //Initialize UI elements
        stepChart = root.findViewById(R.id.stepChart);
        noDataText = root.findViewById(R.id.noDataText);
        btnToday = root.findViewById(R.id.btnToday);
        btnTomorrow = root.findViewById(R.id.btnTomorrow);
        btnViewMore = root.findViewById(R.id.btnViewMore);
        btnAnalyticalInfo = root.findViewById(R.id.btn_Analytical_Info);

        tvHighPrice = root.findViewById(R.id.tvHighPrice);
        tvLowPrice = root.findViewById(R.id.tvLowPrice);
        tvAvgPrice = root.findViewById(R.id.tvAvgPrice);
        tvDailyPricingInfoTitle = root.findViewById(R.id.tvDailyPricingInfoTitle);
        tvThresholdHighPrice = root.findViewById(R.id.tvThresholdHighPrice);
        tvThresholdLowPrice = root.findViewById(R.id.tvThresholdLowPrice);
        tvHighRatesHours = root.findViewById(R.id.tvHighRatesHours);

	// Set click listeners for buttons to load chart data
        btnToday.setOnClickListener(v -> loadChartDataFor("today"));
        btnTomorrow.setOnClickListener(v -> loadChartDataFor("tomorrow"));

	// Fetch price data on fragment load
        fetchPriceData(); 
        fetchThresholdData(); // Fetch threshold data
        fetchHighRatesHours(); // Fetch high rate hours

        // Navigate to Pricing Details page on button click
        btnViewMore.setOnClickListener(v -> {
            NavHostFragment.findNavController(HomeFragment.this)
                    .navigate(R.id.action_homeFragment_to_pricingDetailsFragment);
        });

        // Navigate to Analytical Information Page on button click 
       btnAnalyticalInfo.setOnClickListener(v -> {
            NavHostFragment.findNavController(HomeFragment.this)
                    .navigate(R.id.action_homeFragment_to_analyticalInfoFragment);
        });

        return root;
    }

    public void onResume() {
        super.onResume();
        handler.post(runnable); // Start the handler when the fragment is visible
    }

    @Override
    public void onPause() {
        super.onPause();
        handler.removeCallbacks(runnable); // Stop the handler when the fragment is not visible
    }

    @Override
    public void onViewCreated(View view, Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        // Initialize the handler and runnable
        handler = new Handler();
        runnable = new Runnable() {
            @Override
            public void run() {
                checkAndRefreshChart();
                // Re-post the runnable to be called again after the interval
                handler.postDelayed(this, INTERVAL);
            }
        };
        // Start the first runnable task
        handler.post(runnable);
    }

    // Fetch price data from the server
    private void fetchPriceData() {
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
        apiService.getPriceData().enqueue(new Callback<List<PriceData>>() {
            @Override
            public void onResponse(Call<List<PriceData>> call, Response<List<PriceData>> response) {
                if (response.isSuccessful() && response.body() != null) {
			// Filter data by date
                    filterDataByDate(response.body());
                } else {
			// Display no data message if response is unsuccessful
                    displayNoDataMessage();
                }
            }

            @Override
            public void onFailure(Call<List<PriceData>> call, Throwable t) {
                Toast.makeText(getContext(), "Failed to load data", Toast.LENGTH_SHORT).show();
            }
        });
    }

    // Filter data by date and allocate the data to Today array and Tomorrow array
    private void filterDataByDate(List<PriceData> data) {
        todayData = new ArrayList<>();
        tomorrowData = new ArrayList<>();

	// Get today's and tomorrow's dates
        Calendar calendar = Calendar.getInstance();
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(calendar.getTime());
        calendar.add(Calendar.DATE, 1);
        String tomorrow = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(calendar.getTime());

        // Allocate data to todayData and tomorrowData based on the validFromDate
        for (PriceData priceData : data) {
            if (today.equals(priceData.getValidFromDate())) {
                todayData.add(priceData);
            } else if (tomorrow.equals(priceData.getValidFromDate())) {
                tomorrowData.add(priceData);
            }
        }
        // Load chart data for today by default
        loadChartDataFor("today");

    }

    // Load chart data for the specified day (today or tomorrow)
    private void loadChartDataFor(String day) {
        //If day = today, assign today data to chartData, otherwise assign tomorrow data to chartData
        List<PriceData> chartData = day.equals("today") ? todayData : tomorrowData;
        isToday = day.equals("today") ? true : false;  // Custom LineChart Renderer should be set based on the current data displayed

        if (chartData.isEmpty()) {
            // Display no data message and clear daily pricing info if no data is available
            displayNoDataMessage();
            displayDailyPricingInfo(new ArrayList<>());
        } else {
            // Hide no data message and display step chart
            noDataText.setVisibility(View.GONE);
            stepChart.setVisibility(View.VISIBLE);
            // Display step chart and daily pricing info
            displayStepChart(chartData);
            displayDailyPricingInfo(chartData);
        }
        // Update button styles based on the selected day
        updateButtonStyles(day);
    }

    // Display the step chart with the given data
    private void displayStepChart(List<PriceData> chartData) {
        List<Entry> entries = new ArrayList<>();
        float totalPrice = 0;
        float low = Float.MAX_VALUE;

        Map<Integer, String> timeLabels = new HashMap<>(); // Store labels by index

        for (int i = 0; i < chartData.size(); i++) {
            try {
                float price = Float.parseFloat(chartData.get(i).getValueIncVat());
                totalPrice += price;
                low = Math.min(low, price);

                // Add entries to dataset and map the x-axis position to the from_time`
                entries.add(new Entry(i, price));
                timeLabels.put(i, chartData.get(i).getFromTime()); // Save from_time by position

            } catch (NumberFormatException e) {
                Toast.makeText(getContext(), "Invalid price data", Toast.LENGTH_SHORT).show();
            }
        }

        // Get Y-axis minimum value when lowest price < 0
        lowestPrice = 0;
        if (low < 0 ) {
            lowestPrice = Math.round(low-2);
        }

        // Calculate the average price
        float averagePrice = totalPrice / entries.size();

	    // Create dataset for the step chart
        LineDataSet lineDataSet = new LineDataSet(entries, "Price (VAT incl)");
        LineDataSet avgDataSet = new LineDataSet(averageEntries(averagePrice, entries.size()), "Average Price");
        lineDataSet.setColor(Color.BLUE);
        lineDataSet.setDrawValues(false); // Do not draw values on the line chart
        lineDataSet.setDrawCircles(false); // Do not draw circles on data points
        lineDataSet.setMode(LineDataSet.Mode.STEPPED); // Set line as a step chart

        // Set X-axis properties
        // Customize X-axis
        XAxis xAxis = stepChart.getXAxis();
        xAxis.setGranularity(1f); // Only show the defined labels
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        xAxis.setLabelCount(6, true); // Set label count
        xAxis.setValueFormatter(new MyXAxisValueFormatter(timeLabels)); // Apply custom formatter
        xAxis.setAxisMinimum(0); // Start from index 0
        xAxis.setAxisMaximum(chartData.size() - 1); // End at the last index
        //xAxis.setDrawGridLines(false);

        // Customize Y-axis
        YAxis yAxis = stepChart.getAxisLeft();

        // Start Y-axis, if the lowest value is < 0 set Y-axis minimum to lowest value
        if (lowestPrice.intValue() < 0) {
            yAxis.setAxisMinimum(lowestPrice);
        } else {
            yAxis.setAxisMinimum(0); // Start Y-axis from 0
        }

        yAxis.setDrawGridLines(true);
        yAxis.setGranularity(15f); // Space out labels by 15
        // Disable right Y-axis
        stepChart.getAxisRight().setEnabled(false);
        stepChart.getDescription().setText("");

        // Create average line data
        avgDataSet.setColor(Color.MAGENTA);
        avgDataSet.setDrawCircles(false);
        avgDataSet.setLineWidth(2f);
        avgDataSet.enableDashedLine(10f, 10f, 0f);
        avgDataSet.setDrawValues(false); // Do not draw values on the line chart
        avgDataSet.setDrawCircles(false); // Do not draw circles on data points

        //Custom renderer to indicate the current price for the chart
        int highlightColor = Color.argb(100, 200, 200, 200); // semi-transparent gray
        float highlightWidth = 2f; // width of the highlight bar
        int highlightAlpha = 100; // alpha transparency of the highlight bar

        CustomLineChartRenderer customRenderer = new CustomLineChartRenderer(stepChart, highlightColor, highlightWidth, highlightAlpha, timeLabels);
        stepChart.setRenderer(customRenderer);

	    // Set data to the step chart
        LineData lineData = new LineData(lineDataSet, avgDataSet);
        stepChart.setData(lineData);
        stepChart.invalidate();
    }

    // Display the Daily Pricing Info
    private void displayDailyPricingInfo(List<PriceData> data) {
        if (data.isEmpty()) {
            // Display placeholder text if no data is available
            tvHighPrice.setText("--");
            tvLowPrice.setText("--");
            tvAvgPrice.setText("--");
            return;
        }

        //Initialize the high, low and avg variables
        float high = 0, low = Float.MAX_VALUE, avg = 0;
        for (PriceData priceData : data) {
            float price = 0;
            try {
                price = Float.parseFloat(priceData.getValueIncVat());
            } catch (NumberFormatException e) {
                Toast.makeText(getContext(), "Invalid price data", Toast.LENGTH_SHORT).show();
                continue;
            }
            // Compare the to get the high, low and avg price
            high = Math.max(high, price);
            low = Math.min(low, price);
            avg += price;
        }
        // Calculate the average price
        avg /= data.size();

        // assign the value to the text fields
        tvHighPrice.setText(String.valueOf(high));
        tvLowPrice.setText(String.valueOf(low));
        tvAvgPrice.setText(String.valueOf(avg));
    }

    // Display the no data message
    private void displayNoDataMessage() {
        stepChart.setVisibility(View.GONE);
        noDataText.setVisibility(View.VISIBLE);
        noDataText.setText("Unit rates not available yet. We normally get these at around 4:30pm today. Please try again in a couple of hours.");
    }

    // Update button styles based on the selected day
    private void updateButtonStyles(String day) {
        if (day.equals("today")) {
            tvDailyPricingInfoTitle.setText("Daily Pricing Info for Today");
            btnTomorrow.setBackgroundColor(Color.WHITE);
            btnTomorrow.setTextColor(Color.BLACK);
            btnToday.setBackgroundColor(getResources().getColor(R.color.buttonColor));
            btnToday.setTextColor(Color.WHITE);
        } else {
            tvDailyPricingInfoTitle.setText("Daily Pricing Info for Tomorrow");
            btnToday.setBackgroundColor(Color.WHITE);
            btnToday.setTextColor(Color.BLACK);
            btnTomorrow.setBackgroundColor(getResources().getColor(R.color.buttonColor));
            btnTomorrow.setTextColor(Color.WHITE);
        }
    }

    // Generate entries for the average price line
    private List<Entry> averageEntries(float averagePrice, int size) {
        List<Entry> entries = new ArrayList<>();
        for (int i = 0; i < size; i++) {
            entries.add(new Entry(i, averagePrice));
        }
        return entries;
    }

    // Custom formatter for X-axis labels
    //Reference : https://weeklycoding.com/mpandroidchart-documentation/formatting-data-values/
    private class MyXAxisValueFormatter extends ValueFormatter {
        private final Map<Integer, String> labels;

        MyXAxisValueFormatter(Map<Integer, String> labels) {
            this.labels = labels;
        }

        //override this for custom formatting of XAxis labels
        @Override
        public String getAxisLabel(float value, AxisBase axis) {
            return labels.getOrDefault((int) value, ""); // Show from_time label or empty if not found
        }
    }

    // Send GET Node JS request and load Threshold data for display
    private void fetchThresholdData() {
        //Log.d("HomeFragment", "Fetching threshold data...");
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
        apiService.getThresholdData().enqueue(new Callback<List<ThresholdData>>() {
            @Override
            public void onResponse(Call<List<ThresholdData>> call, Response<List<ThresholdData>> response) {
                //Log.d("THomeFragment", "Threshold Response Code: " + response.code());
                if (response.isSuccessful() && response.body() != null) {
                    List<ThresholdData> thresholds = response.body();

                    // Assuming you want to get the first item in the list
                    if (!thresholds.isEmpty()) {
                        ThresholdData thresholdData = thresholds.get(0); // Get the first ThresholdData object
                        double highPrice = thresholdData.getHighPrice();
                        double lowPrice = thresholdData.getLowPrice();
                        // format the data to display 4 decimal places
                        String formattedHighPrice = String.format("%.4f", highPrice);
                        String formattedLowPrice = String.format("%.4f", lowPrice);

                        //Log.d("HomeFragment", "High Price: " + formattedHighPrice);
                        //Log.d("HomeFragment", "Low Price: " + formattedLowPrice);

                        // Assign value to the text fields
                        tvThresholdHighPrice.setText(formattedHighPrice);
                        tvThresholdLowPrice.setText(formattedLowPrice);

                        // You can now use highPrice and lowPrice as needed
                    } else {
                        Log.e("HomeFragment", "No threshold data found in the response");
                    }
                } else {
                    Log.e("HomeFragment", "Threshold data not available");
                }
            }

            @Override
            public void onFailure(Call<List<ThresholdData>> call, Throwable t) {
                Log.e("HomeFragment", "Failed to load threshold data", t);
            }
        });
    }

    // Send GET Node JS request and load High Rate hours distribution data for display
    private void fetchHighRatesHours() {
        //Log.d("HomeFragment", "Fetching high price hours...");
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
        apiService.getHighPriceHours().enqueue(new Callback<List<HighHour>>() {
            @Override
            public void onResponse(Call<List<HighHour>> call, Response<List<HighHour>> response) {
                //Log.d("HomeFragment", "High Price Hours  Response Code: " + response.code());
                if (response.isSuccessful() && response.body() != null) {
                    // Get High Hour Data
                    List<HighHour> highHours = response.body();
                    StringBuilder hoursString = new StringBuilder(); // Initialize StringBuilder

                    // Build a string for display
                    for (HighHour hour : highHours) {
                        int highHour = hour.getHighHour();
                        hoursString.append(highHour).append(", "); // Append high hour
                    }

                    // Remove the last comma and space if there are high hours
                    if (hoursString.length() > 2) {
                        hoursString.setLength(hoursString.length() - 2);
                    }
                    // Assign the hours string tp text field
                    tvHighRatesHours.setText("High price hours : " + hoursString.toString());
                } else {
                    Log.e("HomeFragment", "High price hours not available");
                }
            }

            @Override
            public void onFailure(Call<List<HighHour>> call, Throwable t) {
                Log.e("HomeFragment", "Failed to load high price hours", t);
            }
        });
    }

    public class CustomLineChartRenderer extends LineChartRenderer {

        // Paint objects for highlighting and label text
        private final Paint highlightPaint;
        private final int highlightColor;    // Color of the highlight area
        private final float highlightWidth;  // Width of the highlight area
        private final int highlightAlpha;  // Alpha value for the highlight area transparency
        private final Paint labelPaint;  // Paint object for label text
        private final Map<Integer, String> timeLabels;  // Map holding time labels

        // Constructor to initialize the renderer with chart, highlight color, width, and labels
        public CustomLineChartRenderer(LineChart chart, int highlightColor, float highlightWidth, int highlightAlpha, Map<Integer, String> timeLabels) {
            // Call the parent constructor with the chart, animator, and view port handler
            super(chart, chart.getAnimator(), chart.getViewPortHandler());
            this.highlightColor = highlightColor;
            this.highlightWidth = highlightWidth;
            this.highlightAlpha = highlightAlpha;
            this.timeLabels = timeLabels;

            // Initialize the fields with the passed values
            highlightPaint = new Paint();
            highlightPaint.setColor(highlightColor); // Set color of the highlight area
            highlightPaint.setAlpha(highlightAlpha); // Set the transparency of the highlight area
            highlightPaint.setStyle(Paint.Style.FILL); // Ensures the paint is filled, not stroked

            // Initialize the label paint object for displaying price labels
            labelPaint = new Paint();
            labelPaint.setColor(Color.rgb(255,0,0));  // Set the label color
            labelPaint.setTextSize(30f); // Set the text size for the label
            labelPaint.setTextAlign(Paint.Align.LEFT); // Set the alignment of the label text
        }

        // Override the drawExtras method to add extra custom drawing (highlight area and labels)
        @Override
        public void drawExtras(Canvas c) {
            super.drawExtras(c); // Call the parent class's method for default extras
            drawHighlightArea(c); // Draw the highlight area with the label
        }

        // Method to draw the highlight area and display the current price label
        private void drawHighlightArea(Canvas c) {
            LineDataProvider lineDataProvider = mChart;  // Get the chart's data provider
            if (lineDataProvider == null) return;   // Return if no data provider

            LineData lineData = lineDataProvider.getLineData();  // Get the line data from the chart
            if (lineData == null) return;  // Return if no line data

            // Ensure this renderer only applies to today's data
            if (!isToday) return;

            // Find the index of the current time
            int currentIndex = getCurrentTimeIndex();

            if (currentIndex != -1) {
                // Get the dataset from the line data
                LineDataSet dataSet = (LineDataSet) lineData.getDataSetByIndex(0);
                if (dataSet == null) return;  // Return if dataset is null

                // Get the entry (data point) for the current time index
                Entry currentEntry = dataSet.getEntryForIndex(currentIndex);
                if (currentEntry == null) return;  // Return if no entry is found

                // Calculate the X positions for the start and end of the highlight area
                float startX = dataSet.getEntryForIndex(currentIndex).getX();
                float endX = startX + 1; // Assuming each entry is spaced by 1 unit

                Transformer transformer = lineDataProvider.getTransformer(YAxis.AxisDependency.LEFT);  // Get the transformer to convert values to pixels

                // Transform the X and Y values to pixel coordinates
                //float[] pts = new float[]{startX, mChart.getYChartMin(), endX, mChart.getYChartMax()};
                float[] pts = new float[]{startX, (float)lowestPrice , endX, mChart.getYChartMax()};
                Log.d("THomeFragment", "pts : " + startX + " : " + mChart.getYChartMin()  + " : " +  endX+ " : " + mChart.getYChartMax() );
                transformer.pointValuesToPixel(pts);

                // Draw the highlight area (a rectangle) on the chart
                RectF rectF = new RectF(pts[0], pts[3], pts[2], pts[1]);
                Log.d("THomeFragment", "rectF: " + pts[0] + " : " + pts[3] + " : " +  pts[2] + " : " + pts[1] );
                c.drawRect(rectF, highlightPaint);

                // Draw the label with the current price
                float[] labelPts = new float[]{startX, currentEntry.getY()};
                transformer.pointValuesToPixel(labelPts);  // Convert label position to pixels
                String label = "Price: " + String.format("%.2f", currentEntry.getY()) + "p"; // Create the label text showing the price

                // Ensure the label is within the canvas bounds
                float labelX = labelPts[0];  // Get the X coordinate of the label
                float labelY = labelPts[1];  // Get the Y coordinate of the label

                // Apply an offset to the Y coordinate to display the label above the bar
                float labelYOffset = 20f;  // Adjust this value to fine-tune the label's position
                labelY = mChart.getYChartMax() ;   // Ensure the label is above the top of the bar

                //Fix label X position to be next to the highlighted area, ensuring the label sits on Left / Right of the bar
                if (labelX > 860) {
                    labelX -= 180;   // Adjust the label position to the left if it's too close to 0 point of the chart
                } else {
                    labelX += 30;  // Adjust the label position to the right if it's too close to end point of the chart
                }

                // Adjust the position to ensure visibility within the canvas
                c.drawText(label, labelX,  labelY, labelPaint);

                // Debug log for visualizing the label's position
                //Log.d("THomeFragment", "drawHighlightArea: " + mChart.getYChartMax());
                //Log.d("THomeFragment", "drawHighlightArea: " + label + " : " + labelX + " : " +  labelY + " : " + labelPaint );
            }
        }

        // Method to find the current time index from the time labels map
        private int getCurrentTimeIndex() {
            // Implement logic to find the current time index
            SimpleDateFormat sdf = new SimpleDateFormat("HH:mm", Locale.getDefault());  // Format for time comparison
            String currentTime = sdf.format(new Date());  // Get the current time as a string
            for (Map.Entry<Integer, String> entry : timeLabels.entrySet()) {
                String time = entry.getValue();
                try {
                    Date chartTime = sdf.parse(time);   // Parse the chart's time label
                    Date now = sdf.parse(currentTime);  // Parse the current time
                    if (chartTime != null && now != null && now.after(chartTime) && now.before(new Date(chartTime.getTime() + 30 * 60 * 1000))) {
                        //Log.d("THomeFragment", "getCurrentTimeIndex: " + entry.getKey() + " : " + chartTime + " : " +  now);
                        // Return the time index if the current time is within a 30-minute window after the chart's time label
                        return entry.getKey();
                    }
                } catch (ParseException e) {
                    e.printStackTrace();  // Handle parsing errors
                }
            }
            return -1;  // Return -1 if no matching time index is found
        }
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        if (handler != null && runnable != null) {
            // Remove the runnable callbacks when the fragment is destroyed
            handler.removeCallbacks(runnable);
        }
    }

    // Function to check the time and refresh the chart if necessary
    private void checkAndRefreshChart() {
        // Get the current time
        Calendar calendar = Calendar.getInstance();
        int minute = calendar.get(Calendar.MINUTE);
        int hour = calendar.get(Calendar.HOUR_OF_DAY);

        // Check if the current time is HH:01 or HH:31
        if ((minute == 1 || minute == 31) && isToday) {
            if (hour == 0 && minute == 1) {
                // When the time is 00:01, reload data as today becomes tomorrow
                fetchPriceData();
            }
            stepChart.invalidate(); // This will trigger the chart to redraw
        }
    }
}
