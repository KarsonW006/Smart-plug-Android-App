package com.example.smart_plug_application.myapp;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.Switch;
import android.widget.TextView;
import com.example.smart_plug_application.R;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;

public class ScheduleAdapter extends RecyclerView.Adapter<ScheduleAdapter.ScheduleViewHolder> {

    private Context context;
    private List<Schedule> schedules;
    private OnItemClickListener onItemClickListener;

    // Interface for item click callbacks
    public interface OnItemClickListener {
        void onItemClick(Schedule schedule, int position);
        void onDeleteClick(Schedule schedule);
        void onToggleClick(Schedule schedule, boolean isEnabled);
        void onModifyClick(Schedule schedule, int position);
    }

    // Constructor to initialize the adapter with context, schedule list, and click listener
    public ScheduleAdapter(Context context, List<Schedule> schedules, OnItemClickListener onItemClickListener) {
        this.context = context;
        this.schedules = schedules;
        this.onItemClickListener = onItemClickListener;

    }

    @NonNull
    @Override
    public ScheduleViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        // Inflate the layout for each item in the RecyclerView
        View view = LayoutInflater.from(context).inflate(R.layout.item_schedule, parent, false);
        return new ScheduleViewHolder(view);
    }

    // Bind the data to the holder and pass the position + 1 for sequence number
    @Override
    public void onBindViewHolder(@NonNull ScheduleViewHolder holder, int position) {
        // Get the schedule at the current position
        Schedule schedule = schedules.get(position);

        // Bind the data to the holder and pass the position + 1 for sequence number
        holder.bind(schedule, onItemClickListener, position + 1,position); // Pass position + 1 for sequence number

        holder.switchEnabled.setOnCheckedChangeListener(null); // Clear previous listener

        holder.switchEnabled.setChecked(schedule.isSwitchEnabled());

        // Set the label based on the switch state
        holder.tvEnableLabel.setText(schedule.isSwitchEnabled() ? "Enable" : "Disable");

        // Set the switch change listener
        holder.switchEnabled.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (buttonView.isPressed()) {
                holder.tvEnableLabel.setText(isChecked ? "Enable" : "Disable"); // Update the label when the switch is toggled
                onItemClickListener.onToggleClick(schedule, isChecked);
            }
        });

        holder.imgDeleteSchedule.setOnClickListener(null); // Clear previous listener
        holder.imgDeleteSchedule.setOnClickListener(v -> onItemClickListener.onDeleteClick(schedule));

        // Set item view click listener
        holder.itemView.setOnClickListener(v -> {
            onItemClickListener.onItemClick(schedule, position);
        });

    }

    // Return the number of schedules
    @Override
    public int getItemCount() {
        return schedules.size();
    }

    public static class ScheduleViewHolder extends RecyclerView.ViewHolder {

        //Define variables
        private TextView tvSchedule;
        private TextView tvStartTime;
        private TextView tvEndTime;
        private TextView tvRunMode;
        private TextView tvThreshold;
        private Switch switchEnabled;
        private ImageView imgDeleteSchedule, imgModifySchedule;
        private TextView tvEnableLabel;

        // Constructor to initialize the views
        public ScheduleViewHolder(@NonNull View itemView) {
            super(itemView);
            //Initialize UI elements
            tvSchedule = itemView.findViewById(R.id.tv_schedule);
            tvStartTime = itemView.findViewById(R.id.tv_start_time);
            tvEndTime = itemView.findViewById(R.id.tv_end_time);
            tvRunMode = itemView.findViewById(R.id.tv_run_mode);
            tvThreshold = itemView.findViewById(R.id.tv_threshold);
            switchEnabled = itemView.findViewById(R.id.switch_enable);
            imgDeleteSchedule = itemView.findViewById(R.id.img_delete_schedule);
            tvEnableLabel= itemView.findViewById(R.id.tv_enable_label);
            imgModifySchedule = itemView.findViewById(R.id.img_modify_schedule);
        }

        // Method to bind data to the views
        public void bind(final Schedule schedule, final OnItemClickListener onItemClickListener, int sequenceNumber, int position) {
            // Use the sequence number instead of schedule ID
            //Assign value
            tvSchedule.setText("Schedule " + sequenceNumber); // Changed to sequence number
            tvStartTime.setText(formatTime(schedule.getStartTime()));
            tvEndTime.setText(formatTime(schedule.getEndTime()));
            tvRunMode.setText(schedule.getRunMode());
            tvThreshold.setText(String.valueOf(schedule.getThreshold()));

            switchEnabled.setChecked("enabled".equalsIgnoreCase(schedule.getStatus()));

            // Update enable label based on switch state
            updateEnableLabel(switchEnabled.isChecked());

            // Set listener for switch state change
            switchEnabled.setOnCheckedChangeListener((buttonView, isChecked) -> {
                if (buttonView.isPressed()) {
                    updateEnableLabel(isChecked); // Update the label when the switch is toggled
                    onItemClickListener.onToggleClick(schedule, isChecked);
                }
            });

            // Set item view click listener
            itemView.setOnClickListener(v -> onItemClickListener.onItemClick(schedule,position));
            imgDeleteSchedule.setOnClickListener(v -> onItemClickListener.onDeleteClick(schedule));
            imgModifySchedule.setOnClickListener(v -> onItemClickListener.onModifyClick(schedule,position));
        }

        // Method to format time to HH:MM
        private String formatTime(String time) {
            // Assuming time is in "HH:MM:SS" format
            return time != null && time.length() >= 5 ? time.substring(0, 5) : time;
        }

        // Method to update the enable label based on the switch state
        private void updateEnableLabel(boolean isEnabled) {
            tvEnableLabel.setText(isEnabled ? "Enable" : "Disable");
        }

    }
}
