package com.example.smart_plug_application.ui.dashboard;

import android.app.AlertDialog;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;
import android.content.Context;
import android.content.SharedPreferences;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;
import androidx.navigation.NavController;
import androidx.navigation.Navigation;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.smart_plug_application.myapp.AddForceScheduleRequest;
import com.example.smart_plug_application.myapp.ApiClient;
import com.example.smart_plug_application.myapp.ApiService;
import com.example.smart_plug_application.R;
import com.example.smart_plug_application.myapp.ChangeStatusRequest;
import com.example.smart_plug_application.myapp.DelScheduleRequest;
import com.example.smart_plug_application.myapp.Device;
import com.example.smart_plug_application.myapp.DeviceStatus;
import com.example.smart_plug_application.myapp.Schedule;
import com.example.smart_plug_application.myapp.ScheduleAdapter;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import android.os.Handler;
import android.widget.CompoundButton;

import org.json.JSONException;
import org.json.JSONObject;

public class DashboardFragment extends Fragment {

    // Define variables for UI elements and data
    private Spinner spinnerDevices;
    private TextView tvDeviceName;
    private TextView tvDeviceIp;
    private RecyclerView recyclerViewSchedules;
    private Button btnAddSchedule, btnDeviceStatus;
    private com.example.smart_plug_application.ui.dashboard.DeviceAdapter deviceAdapter;
    private ScheduleAdapter scheduleAdapter;
    private List<Device> deviceList = new ArrayList<>();
    private List<Schedule> scheduleList = new ArrayList<>();
    private String userid;
    private ImageView imgAddDevice, imgManageDevice;
    private Switch switchForceOn;
    private Handler handler = new Handler();
    private Runnable runnable;
    private ApiService apiService;
    private Device selectedDevice;
    private boolean isUserInteracting = false;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        View view = inflater.inflate(R.layout.fragment_dashboard, container, false);

        // Initialize the API service
        apiService = ApiClient.getRetrofitInstance().create(ApiService.class);

        //Initialize UI elements
        spinnerDevices = view.findViewById(R.id.spinner_devices);
        tvDeviceName = view.findViewById(R.id.tv_device_name);
        tvDeviceIp = view.findViewById(R.id.tv_device_ip);
        recyclerViewSchedules = view.findViewById(R.id.recycler_view_schedules);
        btnAddSchedule = view.findViewById(R.id.btn_add_schedule);
        imgAddDevice= view.findViewById(R.id.img_add_device);
        imgManageDevice= view.findViewById(R.id.img_manage_device);
        btnDeviceStatus = view.findViewById(R.id.btn_device_status);
        switchForceOn = view.findViewById(R.id.switch_forceon);

        // Retrieve userid from SharedPreferences
        SharedPreferences sharedPreferences = getActivity().getSharedPreferences("MyAppPrefs", Context.MODE_PRIVATE);
        userid = sharedPreferences.getString("userid", "");

        // Set up the device adapter for the spinner
        deviceAdapter = new com.example.smart_plug_application.ui.dashboard.DeviceAdapter(getContext(), deviceList);
        spinnerDevices.setAdapter(deviceAdapter);

        // Handle the selection of a device from the spinner
        spinnerDevices.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                // Get the selected device
                selectedDevice = (Device) parent.getItemAtPosition(position);

                // Load details and schedules for the selected device
                loadDeviceDetails(selectedDevice);
                fetchDeviceData();
                loadDeviceSchedules(selectedDevice);
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {
                // Handle nothing selected
            }
        });

        // Set up the schedule adapter for the RecyclerView
        scheduleAdapter = new ScheduleAdapter(getContext(), scheduleList, new ScheduleAdapter.OnItemClickListener() {

            @Override
            public void onItemClick(Schedule schedule, int position) {
                // No specific handling on item click to avoid conflicts with other actions
            }

            @Override
            public void onDeleteClick(Schedule schedule) {
                // Confirm deletion of the schedule
                confirmDeleteSchedule(schedule);
            }

            // Action for toggle click to enable / disable the status
            @Override
            public void onToggleClick(Schedule schedule, boolean isEnabled) {
                // Update the status of the schedule when toggled
                if (isUserInteracting) {
                    updateScheduleStatus(schedule, isEnabled);
                }
            }

            // Action for clicking the modify schedule imageview
            @Override
            public void onModifyClick(Schedule schedule, int position) {
                // Modify the selected schedule if it is not running
                // Get schedule details and pass to DeviceSchedulesFragment
                Schedule selectedSchedule = scheduleList.get(position);

                if (!selectedSchedule.getStatus().equals("Running") ) {
                    try {
                        Bundle args = new Bundle();
                        args.putString("action", "modify_schedule");
                        args.putInt("schedule_id", selectedSchedule.getScheduleId()); // Assuming schedule has an ID
                        args.putString("device_ip", selectedDevice.getDeviceIp());
                        args.putString("device_name", selectedDevice.getDeviceName());

                        // Get the NavController
                        NavController navController = Navigation.findNavController(requireActivity(), R.id.nav_host_fragment_activity_main);
                        // Navigate to the DeviceSchedulesFragment
                        navController.navigate(R.id.navigation_deviceschedules, args);
                    } catch (Exception e) {
                        Log.e("DashboardFragment", "manage_device - Navigation error: " + e.getMessage());
                    }
                } else {
                    Toast.makeText(getActivity(), "Schedule is now running, modification is not allowed!", Toast.LENGTH_SHORT).show();
                }
            }

        });

        // Set recyclerViewSchedules
        recyclerViewSchedules.setLayoutManager(new LinearLayoutManager(getContext()));
        recyclerViewSchedules.setAdapter(scheduleAdapter);

        // Handle clicking the manage device imageview
        imgManageDevice.setOnClickListener(v -> {
            try {
                // Navigate to DeviceSchedulesFragment
                Bundle args = new Bundle();
                args.putString("action", "manage_device");
                args.putString("device_ip", selectedDevice.getDeviceIp());
                args.putString("device_name", selectedDevice.getDeviceName());

                // Get the NavController
                NavController navController = Navigation.findNavController(requireActivity(), R.id.nav_host_fragment_activity_main);
                // Navigate to the DeviceSchedulesFragment
                navController.navigate(R.id.navigation_deviceschedules, args);
            } catch (Exception e) {
                Log.e("DashboardFragment", "manage_device - Navigation error: " + e.getMessage());
            }

        });

        // Handle clicking the add device image view
        imgAddDevice.setOnClickListener(v -> {
            try {
                // Create a Bundle to pass any arguments if needed
                Bundle args = new Bundle();
                args.putString("action", "add_device");

                // Get the NavController
                NavController navController = Navigation.findNavController(requireActivity(), R.id.nav_host_fragment_activity_main);
                // Navigate to the DeviceSchedulesFragment
                navController.navigate(R.id.navigation_deviceschedules, args);
            } catch (Exception e) {
                Log.e("DashboardFragment", "add_device - Navigation error: " + e.getMessage());
            }
        });

        // Handle clicking the add schedule button
        btnAddSchedule.setOnClickListener(v -> {
            try {
                // Navigate to add schedule
                Bundle args = new Bundle();
                args.putString("action", "add_schedule");
                args.putString("device_ip", selectedDevice.getDeviceIp());

                // Get the NavController
                NavController navController = Navigation.findNavController(requireActivity(), R.id.nav_host_fragment_activity_main);
                // Navigate to the DeviceSchedulesFragment
                navController.navigate(R.id.navigation_deviceschedules, args);
            } catch (Exception e) {
                Log.e("DashboardFragment", "add_schedule - Navigation error: " + e.getMessage());
            }
        });

        // Handle toggling the switchForceOn
        switchForceOn.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (switchForceOn.isPressed()) {
                // Avoid triggering logic if changes are programmatically made
                if (!isUserInteracting) return;

                // Check for running schedules
                boolean hasRunningSchedule = false;
                for (Schedule schedule : scheduleList) {
                    if ("Running".equals(schedule.getStatus())) {
                        hasRunningSchedule = true;
                        break;
                    }
                }

                //If any selected device's schedule is running now, it is not allowed to force ON/OFF the device.
                if (hasRunningSchedule) {
                    Toast.makeText(getContext(), "A schedule is running now, it is not allowed to force ON/OFF the device.", Toast.LENGTH_LONG).show();
                    // Revert switch to its original state
                    switchForceOn.setChecked(!isChecked);
                    return;
                }

                // Show confirmation dialog based on switch state
                String message = isChecked
                        ? "Are you sure force to switch ON the device?"
                        : "Are you sure force to switch OFF the device?";
                showConfirmationDialog(isChecked, switchForceOn);
            }
        });

        // call function to load device to the spinner
        loadDevices();

        // Start data fetch timer for periodic updates
        startDataFetchTimer();
        return view;
    }

    // Load the list of devices into the spinner
    private void loadDevices() {
        apiService.getDevicesList(userid).enqueue(new Callback<List<Device>>() {
            @Override
            public void onResponse(Call<List<Device>> call, Response<List<Device>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    // Clear the current list and add new devices
                    deviceList.clear();
                    deviceList.addAll(response.body());
                    deviceAdapter.notifyDataSetChanged();

                    // Automatically select the first device if available
                    if (!deviceList.isEmpty()) {
                        spinnerDevices.setSelection(0);
                        selectedDevice = deviceList.get(0); // Set the first device as selected

                        fetchDeviceData(); // Fetch data for device status for the first device
                    } else {
                        Toast.makeText(getContext(), "No devices found", Toast.LENGTH_SHORT).show();
                    }
                } else {
                    Log.d("DashboardFragment", "Response unsuccessful or body is null");
                }
            }
            // handle failure case
            @Override
            public void onFailure(Call<List<Device>> call, Throwable t) {
                Log.e("DashboardFragment", "Failed to load devices", t);
            }
        });
    }

    // Fetch device on status data from the API for UI display
    private void fetchDeviceData() {
        //Log.d( "DashboardFragment ", "userid -selectedDevice" + userid + " - " + selectedDevice.getDeviceIp());
        //In case the selectedDevice has not been assigned, read the Textview tvDeviceIp value to get the device ip
        String deviceip;
        if (selectedDevice == null) {
            deviceip = tvDeviceIp.getText().toString();
        } else {
            deviceip = selectedDevice.getDeviceIp();
        }
        // Call API to get selected device status
        apiService.getDeviceStatus(userid, deviceip).enqueue(new Callback<List<DeviceStatus>>() {
            @Override
            public void onResponse(@NonNull Call<List<DeviceStatus>> call, @NonNull Response<List<DeviceStatus>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<DeviceStatus> deviceStatusList = response.body();

                    if (deviceStatusList != null && !deviceStatusList.isEmpty()) {
                        // Assuming the first device status from the list
                        DeviceStatus deviceStatus = deviceStatusList.get(0);

                        // Update the power status button text and color
                        if (deviceStatus != null) {
                            updateDeviceStatus(deviceStatus);
                            Log.d( "DashboardFragment ", "deviceStatus" + deviceStatus.getDeviceOn());
                        } else {
                            Log.e("DashboardFragment", "Device Status is null");
                        }
                    } else {
                        Log.e("DashboardFragment", "Device status list is empty or null");
                    }
                } else {
                    Log.e("DashboardFragment", "Response unsuccessful or body is null");
                }
            }
            // handle failure case
            @Override
            public void onFailure(Call<List<DeviceStatus>> call, Throwable t) {
                Log.e("DashboardFragment", "Failed to load device status", t);
            }
        });
    }

    //Assign device detail to the textview
    private void loadDeviceDetails(Device device) {
        tvDeviceName.setText(device.getDeviceName());
        tvDeviceIp.setText(device.getDeviceIp());
    }

    //load device schedules
    private void loadDeviceSchedules(Device device) {
        // Set sUserInteracting Flag = false to let program know the changes is programmatically trigger
        isUserInteracting = false;

        // Call API to get selected device schedule
        apiService.getDeviceSchedules(userid, device.getDeviceIp()).enqueue(new Callback<List<Schedule>>() {
            @Override
            public void onResponse(Call<List<Schedule>> call, Response<List<Schedule>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    // Initialize the schedule list
                    scheduleList.clear();

                    // Loop the schedule and assign the setSwitchEnabled which will be set to Enable when status = Pending or Scheduled or Running
                    for (Schedule schedule : response.body()) {
                        // Enable switch if status is "Pending" or "Scheduled"
                        schedule.setSwitchEnabled(schedule.getStatus().equals("Pending") || schedule.getStatus().equals("Scheduled") || schedule.getStatus().equals("Running"));
                    }

                    // Assign data to scheduleList and reset the isUserInteracting Flag
                    scheduleList.addAll(response.body());
                    isUserInteracting = true;
                    scheduleAdapter.notifyDataSetChanged();

                    if (scheduleList.isEmpty()) {
                        Toast.makeText(getContext(), "No schedules found for this device", Toast.LENGTH_SHORT).show();
                    }
                } else {
                    Log.d("DashboardFragment", "Response unsuccessful or body is null");
                }
            }

            // handle on failure case
            @Override
            public void onFailure(Call<List<Schedule>> call, Throwable t) {
                Log.e("DashboardFragment", "Failed to load device schedules", t);
            }
        });
    }

    // Update schedule status when use click the toggle
    private void updateScheduleStatus(Schedule schedule, boolean isEnabled) {
        // If toggle is Enable, schedule status = Pending, otherwise = Disabling
        String status = isEnabled ? "Pending" : "Disabling";
        ChangeStatusRequest request = new ChangeStatusRequest(schedule.getScheduleId(), status);

        // Call API to update schedule status
        apiService.changeStatus(request).enqueue(new Callback<Void>() {
            @Override
            public void onResponse(Call<Void> call, Response<Void> response) {
                if (response.isSuccessful()) {
                    // After update successful, update schedule setSwitchEnabled value ans display message
                    schedule.setSwitchEnabled(isEnabled);
                    Toast.makeText(getContext(), "Status updated successfully", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(getContext(), "Failed to update status", Toast.LENGTH_SHORT).show();
                }
            }

            // handle on failure case
            @Override
            public void onFailure(Call<Void> call, Throwable t) {
                Log.e("DashboardFragment", "Failed to update status", t);
            }
        });
    }

    // Prompt message to confirm delete schedule before take action
    private void confirmDeleteSchedule(Schedule schedule) {
        new AlertDialog.Builder(getContext())
                .setTitle("Confirm Delete")
                .setMessage("Are you sure you want to delete this schedule?")
                .setPositiveButton("Yes", (dialog, which) -> deleteSchedule(schedule))
                .setNegativeButton("No", null)
                .show();
    }

    // Delete selected schedule
    private void deleteSchedule(Schedule schedule) {
        DelScheduleRequest request = new DelScheduleRequest(schedule.getScheduleId());

        // CAll API to mark the selected schedule to status = deleting
        apiService.delSchedule(request).enqueue(new Callback<Void>() {
            @Override
            public void onResponse(Call<Void> call, Response<Void> response) {
                if (response.isSuccessful()) {
                    //Log.d("DashboardFragment - updateScheduleStatus", "selectedDevice : " + selectedDevice);
                    if (selectedDevice != null) {
                        // Refresh the schedule list after deletion
                        loadDeviceSchedules(selectedDevice); // Reload schedules after deletion
                    } else {
                        // display message for device = null
                        Log.e("DashboardFragment", "selectedDevice is null, cannot reload schedules.");
                        Toast.makeText(getContext(), "Unable to reload schedules. Device not selected.", Toast.LENGTH_SHORT).show();
                    }
                    // display for successful case
                    Toast.makeText(getContext(), "Schedule deleted successfully", Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(getContext(), "Failed to delete schedule", Toast.LENGTH_SHORT).show();
                }
            }

            // handle on failure case
            @Override
            public void onFailure(Call<Void> call, Throwable t) {
                Log.e("DashboardFragment", "Failed to delete schedule", t);
            }
        });
    }

    // Update device status based on the received status
    private void updateDeviceStatus(DeviceStatus deviceStatus) {
        String deviceOn = deviceStatus.getDeviceOn();
        // Update the switch and button color based on the device status
        if ("1".equals(deviceOn)) {
            switchForceOn.setChecked(true);
            if (getContext() != null) {
                btnDeviceStatus.setBackgroundColor(ContextCompat.getColor(getContext(), R.color.green)); // Set to green for "ON"
            }
        } else if ("0".equals(deviceOn)) {
            switchForceOn.setChecked(false);
            if (getContext() != null) {
                btnDeviceStatus.setBackgroundColor(ContextCompat.getColor(getContext(), R.color.lightgrey)); // Set to light grey for "OFF"
            }
        } else {
            Log.e("DashboardFragment", "Invalid device status: " + deviceOn);
        }
    }

    // Start a timer for fetching device on status data periodically
    private void startDataFetchTimer() {
        runnable = new Runnable() {
            @Override
            public void run() {
                fetchDeviceData();
                handler.postDelayed(this, 60000); // Fetch data every minute
            }
        };
        handler.post(runnable);
    }

    // Show a confirmation dialog for force ON/OFF action
    private void showConfirmationDialog(boolean isForceOn, CompoundButton switchButton) {
        String action = isForceOn ? "ON" : "OFF";
        new AlertDialog.Builder(getContext())
                .setTitle("Confirmation")
                .setMessage("Are you sure to force to switch " + action + " the device?")
                .setPositiveButton("Yes", (dialog, which) -> {
                    addForceSchedule(isForceOn);
                })
                .setNegativeButton("No", (dialog, which) -> {
                    // Revert the switch to its original state
                    isUserInteracting = false;
                    switchButton.setChecked(!isForceOn);
                    isUserInteracting = true;
                })
                .show();
    }

    // Add a force schedule for switching the device on or off
    private void addForceSchedule(boolean isForceOn) {
        String status = isForceOn ? "Forcing_On" : "Forcing_Off";
        String runMode = "Run-once";

        // Get current time + 1 min
        long currentTimeMillis = System.currentTimeMillis();
        long startTimeMillis = currentTimeMillis + 60 * 1000; // Current time + 1 minute
        String startTime = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(new Date(startTimeMillis));
        String endTime = startTime; // Same for one-time schedules

        // Create a new schedule request
        AddForceScheduleRequest newSchedule = new AddForceScheduleRequest(userid, selectedDevice.getDeviceIp(), startTime, endTime, runMode, status, 999);

        // Call API to add the force schedule
        apiService.addForceSchedule(newSchedule).enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call, Response<ResponseBody> response) {
                if (response.isSuccessful()) {
                    // Update the switch state and display success message
                    Toast.makeText(getContext(), "Force schedule added successfully, the force schedule will be started within 5 minutes.", Toast.LENGTH_SHORT).show();
                    // Reload schedules to reflect changes
                    loadDeviceSchedules(selectedDevice);

                } else {
                    try {
                        // Handle error response from server, specially for the case that the schedule already have pending force on/off scheduled added
                        String errorBody = response.errorBody().string();

                        JSONObject errorObject = new JSONObject(errorBody);
                        String errorMessage = errorObject.optString("error");

                        Toast.makeText(getContext(), "Failed to add force schedule: " + errorMessage, Toast.LENGTH_LONG).show();
                    } catch (IOException e) {
                        // Handle the IOException for the error body
                        Toast.makeText(getContext(), "Error reading error response: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                        Log.e("addForceScheduleError", "IOException while reading error response", e);
                    } catch (JSONException e) {
                        // Handle JSON parsing error for the error response
                        Toast.makeText(getContext(), "Error parsing error response.", Toast.LENGTH_SHORT).show();
                        Log.e("addForceScheduleError", "JSONException while parsing error response", e);
                    }
                    // Revert the switch to its original state due to operation failed
                    switchForceOn.setChecked(!switchForceOn.isChecked());
                }
            }
            // Handle failure to add force schedule
            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                Toast.makeText(getContext(), "Error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        // Remove the runnable callbacks when the fragment is destroyed
        handler.removeCallbacks(runnable);
    }
}
