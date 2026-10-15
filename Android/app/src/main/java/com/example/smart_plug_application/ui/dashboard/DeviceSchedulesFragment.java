package com.example.smart_plug_application.ui.dashboard;

import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import org.json.JSONException;
import org.json.JSONObject;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import com.example.smart_plug_application.R;
import com.example.smart_plug_application.myapp.AddDeviceRequest;
import com.example.smart_plug_application.myapp.AddScheduleRequest;
import com.example.smart_plug_application.myapp.ApiClient;
import com.example.smart_plug_application.myapp.ApiService;
import com.example.smart_plug_application.myapp.DelDeviceRequest;
import com.example.smart_plug_application.myapp.ModifyDeviceRequest;
import com.example.smart_plug_application.myapp.ModifyScheduleRequest;
import com.example.smart_plug_application.myapp.Schedule;

import java.io.IOException;
import java.util.List;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;

public class DeviceSchedulesFragment extends Fragment {
    // Define variables
    private EditText editDeviceIp, editThreshold;
    private TextView tvDevice, tvDeviceName, tvInfoMessage, tvSchedule;
    private ImageView imgSaveDevice, imgDeleteDevice, imgSaveSchedule;
    private Spinner spinnerStartHour, spinnerStartMinute, spinnerEndHour, spinnerEndMinute, spinnerRunMode;
    private String userId, deviceIp, deviceName;
    private boolean isModifyDevice = false;
    private boolean isModifySchedule = false;
    private int scheduleId;
    private LinearLayout fmScheduleDetails;
    private boolean isFetchingScheduleDetails = false;

    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        return inflater.inflate(R.layout.fragment_deviceschedules, container, false);
    }


    @Override
    public void onViewCreated(@NonNull View view,  @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        //Initialize UI elements
        editDeviceIp = view.findViewById(R.id.edit_device_ip);
        editThreshold = view.findViewById(R.id.edit_threshold);
        tvDevice = view.findViewById(R.id.tv_Device);
        tvDeviceName = view.findViewById(R.id.tv_device_name);
        tvInfoMessage = view.findViewById(R.id.tv_info_message);
        tvSchedule = view.findViewById(R.id.tv_Schedule);
        imgSaveDevice = view.findViewById(R.id.img_save_device);
        imgDeleteDevice = view.findViewById(R.id.img_delete_device);
        imgSaveSchedule = view.findViewById(R.id.img_save_schedule);
        spinnerStartHour = view.findViewById(R.id.spinner_start_hour);
        spinnerStartMinute = view.findViewById(R.id.spinner_start_minute);
        spinnerEndHour = view.findViewById(R.id.spinner_end_hour);
        spinnerEndMinute = view.findViewById(R.id.spinner_end_minute);
        spinnerRunMode = view.findViewById(R.id.spinner_run_mode);
        fmScheduleDetails = view.findViewById(R.id.frame_schedule_details);

        // Setup Time Spinner and Run Mode Spinner
        setupTimeSpinners(view);
        setupRunModeSpinners(view);

        // Get userId from SharedPreferences
        SharedPreferences sharedPreferences = getActivity().getSharedPreferences("MyAppPrefs", Context.MODE_PRIVATE);
        userId = sharedPreferences.getString("userid", "");

        //Log.d("DeviceSchedulesFragment", "userId : " + userId);
        // Handle actions based on flags
        Bundle args = getArguments();

        // Get argument value to initialize the UI elements and call appropriate function
        if (args != null) {
            String action = args.getString("action");
            if ("add_device".equals(action)) {
                // assign flag value to initialize the UI elements
                isModifyDevice = false;
                setupForAddDevice();

            } else if ("manage_device".equals(action)) {
                deviceIp = args.getString("device_ip");
                deviceName = args.getString("device_name");
                // assign flag value to initialize the UI elements
                isModifyDevice = true;
                setupForModifyDevice();

            } else if ("add_schedule".equals(action)) {
                deviceIp = args.getString("device_ip");
                deviceName = args.getString("device_name");
                // assign flag value to initialize the UI elements
                isModifySchedule = false;
                setupForAddSchedule();

            } else if ("modify_schedule".equals(action)) {
                scheduleId = args.getInt("schedule_id");
                deviceIp = args.getString("device_ip");
                deviceName = args.getString("device_name");
                // assign flag value to initialize the UI elements
                isModifySchedule =true;
                //Log.d("DeviceSchedulesFragment", "addDevice - userId : " + scheduleId);
                // Fetch and display schedule details here
                setupForModifySchedule();

            }
        }

        // Base on the flag value to call appropriate function to handle modify or add device
        imgSaveDevice.setOnClickListener(v -> {
            // Initialize the tvInfoMessage
            tvInfoMessage.setText("");

            if (isModifyDevice) {
                modifyDevice();
            } else {
                addDevice();
            }
        });

        // handle delete device
        imgDeleteDevice.setOnClickListener(v -> {
            // Initialize the tvInfoMessage
            tvInfoMessage.setText("");
            confirmDeleteDevice();
        });

        // Base on the flag value to call appropriate function to handle modify or add schedule
        imgSaveSchedule.setOnClickListener(v -> {
            // Initialize the tvInfoMessage
            tvInfoMessage.setText("");

            if (isModifySchedule) {
                modifySchedule();
            } else {
                addSchedule();
            }
        });

    }

    // Setup UI elements for Add Device
    private void setupForAddDevice() {
        tvDevice.setText("Add Device");
        editDeviceIp.setText("");
        editDeviceIp.setEnabled(true);
        imgDeleteDevice.setVisibility(View.GONE);
        imgSaveDevice.setVisibility(View.VISIBLE);
        fmScheduleDetails.setVisibility(View.GONE);
    }

    // Setup UI elements for Modify Device
    private void setupForModifyDevice() {
        tvDevice.setText("Modify Device");
        editDeviceIp.setText(deviceIp);
        tvDeviceName.setText(deviceName);
        editDeviceIp.setEnabled(true);

        imgDeleteDevice.setVisibility(View.VISIBLE);
        imgSaveDevice.setVisibility(View.VISIBLE);
        fmScheduleDetails.setVisibility(View.GONE);
    }

    // Setup UI elements for Add Schedule
    private void setupForAddSchedule() {
        tvDevice.setText("Device");
        tvSchedule.setText("Add Schedule");
        editDeviceIp.setText(deviceIp);
        tvDeviceName.setText(deviceName);
        editDeviceIp.setEnabled(false);

        editThreshold.setText(""); // Reset threshold
        imgDeleteDevice.setVisibility(View.GONE);
        imgSaveDevice.setVisibility(View.GONE);
        imgSaveSchedule.setVisibility(View.VISIBLE);
        fmScheduleDetails.setVisibility(View.VISIBLE);
    }

    // Setup UI elements for Modify Schedule
    private void setupForModifySchedule() {
        tvDevice.setText("Device");
        tvSchedule.setText("Modify Schedule");
        editDeviceIp.setText(deviceIp);
        tvDeviceName.setText(deviceName);

        editDeviceIp.setEnabled(false);
        imgDeleteDevice.setVisibility(View.GONE);
        imgSaveDevice.setVisibility(View.GONE);
        imgSaveSchedule.setVisibility(View.VISIBLE);
        fmScheduleDetails.setVisibility(View.VISIBLE);

        // Fetch schedule details from server and set the UI elements accordingly
        if (!isFetchingScheduleDetails) {
            isFetchingScheduleDetails = true;
            fetchScheduleDetails(scheduleId);
        }
    }

    // handle Add device
    private void addDevice() {
        String ip = editDeviceIp.getText().toString();
        //Log.d("DeviceSchedulesFragment", "addDevice : " + ip);

        //Validate the IP cannot be empty
        if (ip.isEmpty()) {
            tvInfoMessage.setText("Device IP cannot be empty.");
            return;
        }

        // validate IP format
        if (!validateIp(ip)) {
            tvInfoMessage.setText("Invalid IP Address.");
            return;
        }
        //Log.d("DeviceSchedulesFragment", "addDevice - userId : " + userId);

        // Call API to add device to database
        AddDeviceRequest request = new AddDeviceRequest(userId, ip);
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
        apiService.addDevice(request).enqueue(new Callback<Void>() {
            @Override
            public void onResponse(Call<Void> call, Response<Void> response) {
                if (response.isSuccessful()) {
                    // If successful, reset the device to empty
                    editDeviceIp.setText("");
                    tvInfoMessage.setText("Device added successfully.  You may back to the Dashboard page to view the changes.");
                } else {
                    tvInfoMessage.setText("Failed to add device, device already exists.");
                }
            }

            @Override
            public void onFailure(Call<Void> call, Throwable t) {
                tvInfoMessage.setText("Error: " + t.getMessage());
            }
        });
    }

    // handle to modify device
    private void modifyDevice() {
        String ip = editDeviceIp.getText().toString();
        String Old_Ip = deviceIp;
        //Log.d("DeviceSchedulesFragment", "addDevice - userId : " + userId);
        //Log.d("DeviceSchedulesFragment", "addDevice - New IP : " + ip);
        //Log.d("DeviceSchedulesFragment", "addDevice - Old_Ip : " + Old_Ip);

        //Validate the IP cannot be empty
        if (ip.isEmpty()) {
            tvInfoMessage.setText("Device IP cannot be empty.");
            return;
        }

        //Validate the IP cannot be same as the old IP
        if (ip.equals(Old_Ip)) {
            tvInfoMessage.setText("Device IP is not chnaged, please enter a new Device IP for modification.");
            return;
        }

        // validate IP format
        if (!validateIp(ip)) {
            tvInfoMessage.setText("Invalid IP Address.");
            return;
        }

        // Call API to modify device to database
        ModifyDeviceRequest request = new ModifyDeviceRequest(userId, ip,Old_Ip);
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
        apiService.modifyDevice(request).enqueue(new Callback<Void>() {
            @Override
            public void onResponse(Call<Void> call, Response<Void> response) {
                if (response.isSuccessful()) {
                    // If successful reset device ip and device name.  Also, set action imageview to invisible to avoid modify again
                    editDeviceIp.setText("");
                    tvDeviceName.setText("");
                    imgSaveSchedule.setVisibility(View.GONE);
                    imgDeleteDevice.setVisibility(View.GONE);
                    tvInfoMessage.setText("Device modified successfully.  You may back to the Dashboard page to view the changes.");
                } else {
                    tvInfoMessage.setText("Failed to modify device, device already exists.");
                }
            }

            @Override
            public void onFailure(Call<Void> call, Throwable t) {
                tvInfoMessage.setText("Error: " + t.getMessage());
            }
        });
    }

    // Prompt message to ask user to confirm delete device before take action
    private void confirmDeleteDevice() {
        new AlertDialog.Builder(getContext())
                .setTitle("Confirm Delete")
                .setMessage("Are you sure you want to delete this device?")
                .setPositiveButton("Yes", (dialog, which) -> deleteDevice())
                .setNegativeButton("No", null)
                .show();
    }

    // handle delete device
    private void deleteDevice() {
        // Call API to delete device
        DelDeviceRequest request = new DelDeviceRequest(userId, deviceIp);
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
        apiService.deleteDevice(request).enqueue(new Callback<Void>() {
            @Override
            public void onResponse(Call<Void> call, Response<Void> response) {
                if (response.isSuccessful()) {
                    // If successful, reset the device ip and device name to empty
                    editDeviceIp.setText("");
                    tvDeviceName.setText("");
                    imgDeleteDevice.setVisibility(View.GONE);
                    imgSaveSchedule.setVisibility(View.GONE);
                    tvInfoMessage.setText("Device deleted successfully. You may back to the Dashboard page, the deleted device will no longer display.");
                } else {
                    tvInfoMessage.setText("Failed to delete device.");
                }
            }

            @Override
            public void onFailure(Call<Void> call, Throwable t) {
                tvInfoMessage.setText("Error: " + t.getMessage());
            }
        });
    }

    // handle add schedule
    private void addSchedule() {
        //Define variable and get vale from input fields
        String startTime = spinnerStartHour.getSelectedItem() + ":" + spinnerStartMinute.getSelectedItem();
        String endTime = spinnerEndHour.getSelectedItem() + ":" + spinnerEndMinute.getSelectedItem();
        String runMode = spinnerRunMode.getSelectedItem().toString();
        //float threshold = Float.parseFloat(editThreshold.getText().toString());

        // If no value input for threshold, default to 999
        float threshold = 0;
        if (editThreshold != null) {
            String thresholdText = editThreshold.getText().toString();

            if (thresholdText.isEmpty()) {
                threshold = 999f; // Set to 999 if empty
            } else {
                try {
                    threshold = Float.parseFloat(thresholdText);
                } catch (NumberFormatException e) {
                    // Handle the case where parsing fails, set to default value
                    threshold = 999f; // set to a default value or handle differently
                }
            }
        }

        // Parse and compare start and end times
        DateTimeFormatter timeFormatter = DateTimeFormatter.ofPattern("HH:mm");
        try {
            LocalTime startTimeStr = LocalTime.parse(startTime, timeFormatter);
            LocalTime endTimeStr = LocalTime.parse(endTime, timeFormatter);

            if (!startTimeStr.isBefore(endTimeStr)) {
                tvInfoMessage.setText("Start time must be before end time");
                //Toast.makeText(this, "Start time must be before end time", Toast.LENGTH_SHORT).show();
                return; // Exit the method if the time comparison is invalid
            }
        } catch (DateTimeParseException e) {
            tvInfoMessage.setText("Invalid time format");
            //Toast.makeText(this, "Invalid time format", Toast.LENGTH_SHORT).show();
            return; // Exit the method if the time parsing fails
        }

        // Call API to add new schedule to database
        AddScheduleRequest request = new AddScheduleRequest(userId, deviceIp, startTime, endTime, runMode, "Pending", threshold);
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);

        apiService.addSchedule(request).enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call, Response<ResponseBody> response) {
                if (response.isSuccessful() && response.body() != null) {
                    try {
                        // Attempt to read the response body
                        String jsonResponse = response.body().string();
                        //Log.d("Add Schedule Response", jsonResponse);

                        JSONObject jsonObject = new JSONObject(jsonResponse);
                        String message = jsonObject.optString("message");

                        // Display message
                        if ("Add new schedule successfully".equals(message)) {
                            tvInfoMessage.setText("Add new schedule successfully.  You may back to the Dashboard page to view the changes.");
                        } else {
                            tvInfoMessage.setText("Add Schedule Failed: " + message);
                        }
                    } catch (IOException e) {
                        // Handle the IOException
                        tvInfoMessage.setText("Error reading response: " + e.getMessage());
                        Log.e("AddScheduleError", "IOException while reading response", e);
                    } catch (JSONException e) {
                        // Handle JSON parsing error
                        tvInfoMessage.setText("Error parsing response.");
                        Log.e("AddScheduleError", "JSONException while parsing response", e);
                    }
                } else {
                    try {
                        // Handle error response, specially for the case that this request time period overlapping with another schedule
                        String errorBody = response.errorBody().string();
                        //Log.d("AddScheduleError", errorBody);
                        JSONObject errorObject = new JSONObject(errorBody);
                        String errorMessage = errorObject.optString("error");

                        tvInfoMessage.setText("Add Schedule Failed: " + errorMessage);
                    } catch (IOException e) {
                        // Handle the IOException for the error body
                        tvInfoMessage.setText("Error reading error response: " + e.getMessage());
                        Log.e("AddScheduleError", "IOException while reading error response", e);
                    } catch (JSONException e) {
                        // Handle JSON parsing error for the error response
                        tvInfoMessage.setText("Error parsing error response.");
                        Log.e("AddScheduleError", "JSONException while parsing error response", e);
                    }
                }
            }

            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                tvInfoMessage.setText("Error: " + t.getMessage());
            }
        });
    }

    //handle modify schedule
    private void modifySchedule() {
        //Define variable and get vale from input fields
        String startTime = spinnerStartHour.getSelectedItem() + ":" + spinnerStartMinute.getSelectedItem();
        String endTime = spinnerEndHour.getSelectedItem() + ":" + spinnerEndMinute.getSelectedItem();
        String runMode = spinnerRunMode.getSelectedItem().toString();
        //float threshold = Float.parseFloat(editThreshold.getText().toString());

        // If no value input for threshold, default to 999
        float threshold = 0;
        if (editThreshold != null) {
            String thresholdText = editThreshold.getText().toString();
            //    float threshold;

            if (thresholdText.isEmpty()) {
                threshold = 999f; // Set to 999 if empty
            } else {
                try {
                    threshold = Float.parseFloat(thresholdText);
                } catch (NumberFormatException e) {
                    // Handle the case where parsing fails, set to default value
                    threshold = 999f; // set to a default value or handle differently
                }
            }
        }

        // Parse and compare start and end times
        DateTimeFormatter timeFormatter = DateTimeFormatter.ofPattern("HH:mm");
        try {
            LocalTime startTimeStr = LocalTime.parse(startTime, timeFormatter);
            LocalTime endTimeStr = LocalTime.parse(endTime, timeFormatter);

            if (!startTimeStr.isBefore(endTimeStr))  {
                tvInfoMessage.setText("Start time must be before end time");
                //Toast.makeText(this, "Start time must be before end time", Toast.LENGTH_SHORT).show();
                return; // Exit the method if the time comparison is invalid
            }
        } catch (DateTimeParseException e) {
            tvInfoMessage.setText("Invalid time format");
            //Toast.makeText(this, "Invalid time format", Toast.LENGTH_SHORT).show();
            return; // Exit the method if the time parsing fails
        }

        // Call API to modify schedule to database
        ModifyScheduleRequest request = new ModifyScheduleRequest(userId, deviceIp, scheduleId, startTime, endTime, runMode, threshold);
        ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
        apiService.modifySchedule(request).enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(Call<ResponseBody> call, Response<ResponseBody> response) {
                if (response.isSuccessful() && response.body() != null) {
                    try {
                        // Attempt to read the response body
                        String jsonResponse = response.body().string();
                        //Log.d("Modify Schedule Response", jsonResponse);

                        JSONObject jsonObject = new JSONObject(jsonResponse);
                        String message = jsonObject.optString("message");

                        //display message
                        if ("Modify schedule successfully".equals(message)) {
                            tvInfoMessage.setText("Modify schedule successfully.  You may back to the Dashboard page to view the changes");
                        } else {
                            tvInfoMessage.setText("Modify Schedule Failed: " + message);
                        }
                    } catch (IOException e) {
                        // Handle the IOException
                        tvInfoMessage.setText("Error reading response: " + e.getMessage());
                        Log.e("ModifyScheduleError", "IOException while reading response", e);
                    } catch (JSONException e) {
                        // Handle JSON parsing error
                        tvInfoMessage.setText("Error parsing response.");
                        Log.e("ModifyScheduleError", "JSONException while parsing response", e);
                    }
                } else {
                    try {
                        // Handle error response, specially for the case that this request time period overlapping with another schedule
                        String errorBody = response.errorBody().string();
                        //Log.d("ModifyScheduleError", errorBody);
                        JSONObject errorObject = new JSONObject(errorBody);
                        String errorMessage = errorObject.optString("error");

                        tvInfoMessage.setText("Modify Schedule Failed: " + errorMessage);
                    } catch (IOException e) {
                        // Handle the IOException for the error body
                        tvInfoMessage.setText("Error reading error response: " + e.getMessage());
                        Log.e("ModifyScheduleError", "IOException while reading error response", e);
                    } catch (JSONException e) {
                        // Handle JSON parsing error for the error response
                        tvInfoMessage.setText("Error parsing error response.");
                        Log.e("ModifyScheduleError", "JSONException while parsing error response", e);
                    }
                }
            }

            @Override
            public void onFailure(Call<ResponseBody> call, Throwable t) {
                tvInfoMessage.setText("Error: " + t.getMessage());
            }
        });
    }

    // validate device ip format
    private boolean validateIp(String ip) {
        // Validate IP format here
        // Simple IP validation logic
        String regex = "^(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}$";

        //Log.d("DeviceSchedulesFragment", "validateIp : " + regex);
        return ip.matches(regex);
    }

    // Send request to get schedule detail for modify schedule case and fetch data
    private void fetchScheduleDetails(int scheduleId) {
        if (isFetchingScheduleDetails = true) {
            //Call API to get selected schedule detail
            ApiService apiService = ApiClient.getRetrofitInstance().create(ApiService.class);
            //Log.d("DeviceSchedulesFragment", "fetchScheduleDetails - scheduleId : " + scheduleId);
            apiService.getScheduleDetails(scheduleId).enqueue(new Callback<List<Schedule>>() {
                @Override
                public void onResponse(Call<List<Schedule>> call, Response<List<Schedule>> response) {
                    if (response.isSuccessful() && response.body() != null && !response.body().isEmpty()) {
                        Schedule schedule = response.body().get(0);// Get the first schedule from the list
                        //Log.d("DeviceSchedulesFragment", "fetchScheduleDetails - scheduleId : " + scheduleId);
                        // Update UI elements with schedule data
                        updateUIWithScheduleDetails(schedule);
                    } else {
                        tvInfoMessage.setText("Failed to fetch schedule details.");
                    }
                }

                @Override
                public void onFailure(Call<List<Schedule>> call, Throwable t) {
                    tvInfoMessage.setText("Error: " + t.getMessage());
                }
            });
        }
        isFetchingScheduleDetails = false;
    }

    // Update schedule data for modify case
    private void updateUIWithScheduleDetails(Schedule schedule) {
        if (spinnerStartHour != null) {
            spinnerStartHour.setSelection(getHourIndex(schedule.getStartTime()));
        }

        if (spinnerStartMinute != null) {
            spinnerStartMinute.setSelection(getMinuteIndex(schedule.getStartTime()));
        }
        if (spinnerEndHour != null) {
            spinnerEndHour.setSelection(getHourIndex(schedule.getEndTime()));
        }
        if (spinnerEndMinute != null) {
            spinnerEndMinute.setSelection(getMinuteIndex(schedule.getEndTime()));
        }
        if (spinnerRunMode != null) {
            spinnerRunMode.setSelection(getRunModeIndex(schedule.getRunMode()));
        }

        if (editThreshold != null) {
            editThreshold.setText(String.valueOf(schedule.getThreshold()));
        }
    }


    // get the index for hour spinners
    private int getHourIndex(String time) {
        String[] parts = time.split(":");
        if (parts.length > 0) {
            int hour = Integer.parseInt(parts[0]);
            if (hour >= 0 && hour < 24) {
                return hour; // Ensure hour is within the range for the spinner
            }
        }
        return 0; // Default to 0 if parsing fails
    }

    // get the index for minute spinners
    private int getMinuteIndex(String time) {
        String[] parts = time.split(":");
        if (parts.length > 1) {
            int minute = Integer.parseInt(parts[1]);
            // Assuming minute spinner has values: 0, 15, 30, 45
            switch (minute) {
                case 0: return 0;
                case 15: return 1;
                case 30: return 2;
                case 45: return 3;
            }
        }
        return 0; // Default to 0 if parsing fails or minute is invalid
    }

    // get the index for run mode spinners
    private int getRunModeIndex(String runMode) {
        // Define run modes and their corresponding indices
        String[] runModes = {"Run-once", "Repeat"}; // Example run modes

        for (int i = 0; i < runModes.length; i++) {
            if (runModes[i].equals(runMode)) {
                return i; // Return the index if it matches
            }
        }
        return 0; // Default to 0 if no match found
    }

    // Setup time spinners
    private void setupTimeSpinners(View view) {
        // Setup hour adapter using pre-defined hour array
        ArrayAdapter<CharSequence> hourAdapter = ArrayAdapter.createFromResource(
                getContext(), R.array.hours_array, android.R.layout.simple_spinner_item);
        hourAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerStartHour.setAdapter(hourAdapter);
        spinnerEndHour.setAdapter(hourAdapter);

        // Setup minute adapter using pre-defined minute array
        ArrayAdapter<CharSequence> minuteAdapter = ArrayAdapter.createFromResource(
                getContext(), R.array.minutes_array, android.R.layout.simple_spinner_item);
        minuteAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerStartMinute.setAdapter(minuteAdapter);
        spinnerEndMinute.setAdapter(minuteAdapter);
    }

    // Setup run mode spinner
    private void setupRunModeSpinners(View view) {

        String[] runMode = {"Run-once", "Repeat"}; // Ensure this has at least 4 items
        // Log the size
        //Log.d("SpinnerData", "Size: " + runMode.length);
        try {
            // Setup run mode adapter
            ArrayAdapter<String> runModeAdapter = new ArrayAdapter<>(getContext(), android.R.layout.simple_spinner_item, runMode);
            runModeAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);

            spinnerRunMode.setAdapter(runModeAdapter);

        } catch (Exception e) {
            Log.e("SpinnerError", "Error setting up Spinner: " + e.getMessage());
        }

    }
}
