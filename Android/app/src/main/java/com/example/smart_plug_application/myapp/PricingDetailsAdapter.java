package com.example.smart_plug_application.myapp;

import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;
import com.example.smart_plug_application.R;
import android.util.Log;

public class PricingDetailsAdapter extends RecyclerView.Adapter<PricingDetailsAdapter.ViewHolder> {

    // List to hold pricing data
    private List<PriceData> priceDataList;

	// Constructor to initialize the adapter with the price data list
    public PricingDetailsAdapter(List<PriceData> priceDataList) {
        this.priceDataList = priceDataList;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
	// Inflate the layout for each item in the RecyclerView
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_price_data, parent, false);
        return new ViewHolder(view); // Return a new ViewHolder
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        // Calculate the midpoint to divide the data into two halves
        int half = (priceDataList.size() + 1) / 2;

        // Get the data for the left side of the row
        PriceData leftData = priceDataList.get(position);
        holder.bindData(leftData, holder.periodLeft, holder.priceLeft);

        // Check if there is corresponding data for the right side of the row
        if (position + half < priceDataList.size()) {
            PriceData rightData = priceDataList.get(position + half);
            holder.bindData(rightData, holder.periodRight, holder.priceRight);
        } else {
            // If no data for the right side, clear the text views
            holder.periodRight.setText("");
            holder.priceRight.setText("");
        }
    }

    // Return the number of items to be displayed (half the size of the list, rounded up)
    @Override
    public int getItemCount() {
        return (priceDataList.size() + 1) / 2;
    }

    // ViewHolder class to hold and manage the views for each item
    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView periodLeft, priceLeft, periodRight, priceRight;

	// Constructor to initialize the views
        ViewHolder(@NonNull View itemView) {
            super(itemView);		
            periodLeft = itemView.findViewById(R.id.periodLeft);
            priceLeft = itemView.findViewById(R.id.priceLeft);
            periodRight = itemView.findViewById(R.id.periodRight);
            priceRight = itemView.findViewById(R.id.priceRight);
        }

	// Method to bind data to the views
        void bindData(PriceData data, TextView period, TextView price) {
            // Set the period text
            String periodText = data.getFromTime() + " - " + data.getToTime();
            period.setText(periodText);

		// Set the price text
            String priceText = String.format("%.4f", Double.parseDouble(data.getValueIncVat()));
            price.setText(priceText);

            // Set the background color based on the price category
            int color = getColorForCategory(data.getPriceCategory());
            price.setBackgroundColor(color);
        }

        // Method to get color based on the price category
        int getColorForCategory(String category) {
            switch (category) {
                case "Above Threshold":
                    return Color.rgb(255, 99, 71);
                case "Below Threshold":
                    return Color.rgb(60, 179, 113);
                case "Within Threshold":
                    return Color.rgb(255, 165, 0);
                default:
                    return Color.WHITE;
            }
        }
    }
}
