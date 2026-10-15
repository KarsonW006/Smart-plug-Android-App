package com.example.smart_plug_application.ui.dashboard;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.example.smart_plug_application.myapp.Device;

import java.util.List;


public class DeviceAdapter extends ArrayAdapter<Device> {

    public DeviceAdapter(@NonNull Context context, @NonNull List<Device> devices) {
        super(context, 0, devices);
    }

    //For the non-expanded state of the spinner, used to create and return the view for the currently selected item in the spinner.
    @NonNull
    @Override
    public View getView(int position, @Nullable View convertView, @NonNull ViewGroup parent) {
        if (convertView == null) {
            convertView = LayoutInflater.from(getContext()).inflate(android.R.layout.simple_spinner_item, parent, false);
        }
        Device device = getItem(position);
        TextView textView = convertView.findViewById(android.R.id.text1);
        if (device != null) {
            textView.setText(device.getDeviceName());
        }
        return convertView;
    }

    // For the spinner dropdown is shown, used to create and return the view for each item in the dropdown list when the spinner is expanded.
    @Override
    public View getDropDownView(int position, @Nullable View convertView, @NonNull ViewGroup parent) {
        if (convertView == null) {
            convertView = LayoutInflater.from(getContext()).inflate(android.R.layout.simple_spinner_dropdown_item, parent, false);
        }
        Device device = getItem(position);
        TextView textView = convertView.findViewById(android.R.id.text1);
        if (device != null) {
            // Assign device name to the spinner
            textView.setText(device.getDeviceName());
        }
        return convertView;
    }

}

