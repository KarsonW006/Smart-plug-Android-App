package com.example.smart_plug_application.myapp;

// Set class for price data
public class PriceData {
    private String value_inc_vat;
    private String valid_from_date;
    private String from_time;
    private String to_time;
    private String price_category;

    // Getters  for get values
    public String getValueIncVat() {
        return value_inc_vat;
    }

    public String getValidFromDate() {
        return valid_from_date;
    }

    public String getFromTime() {
        return from_time;
    }

    public String getToTime() { return to_time; }

    public String getPriceCategory() {
        return price_category;
    }
}
