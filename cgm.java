package com.example.a535meal;

public class cgm implements Model2 {

    private static final int SECOND = 1000;
    private static final int MINUTE = 60 * SECOND;
    private static final int HOUR = 60 * MINUTE;
    TreeMap<Long, Double> cgmRecords;
    TreeMap<Long, Integer> bolusRecords;
    TreeMap<Long, Integer> carbRecords;
    TreeMap<Long, Integer> activityRecords;
    long trackTime;
    SimpleDateFormat excel;
    SimpleDateFormat sd;

    public cgm {Context context)  {
        sd = new SimpleDateFormat("dd/MM/yyyy HH:mm");
        excel = new SimpleDateFormat("yyyy-MM-dd HH:mm");

        cgmRecords = new TreeMap<>();
        bolusRecords = new TreeMap<>();
        carbRecords = new TreeMap<>();
        activityRecords = new TreeMap<>();

        InputStream cgmStream = null;
        InputStream bolusStream = null;
        InputStream carbsStream = null;
        InputStream activityStream = null;

        //Loads data.
        try {
            AssetManager manager = context.getAssets();
            cgmStream = manager.open(".csv");
            bolusStream = manager.open(".csv");
            carbsStream = manager.open(".csv");
            activityStream = manager.open("csv");
        }
        catch (IOException e) {
            Log.v("tag", e.getMessage());
        }

        try {
            parseFile(cgmStream, excel, cgmRecords, true);
            parseFile(bolusStream, excel, bolusRecords, false);
            parseFile(carbsStream, sd, carbRecords, false);
            parseFile(activityStream, excel, activityRecords, false);
        }
        catch (ParseException e) {
            Log.v("tag", e.getMessage());
        }
        ArrayList<Long> activityDateList = new ArrayList<>();
        for (long date : activityRecords.keySet()) {
            double value = activityRecords.get(date);
            if (value==0) {
                activityDateList.add(date);
            }
        }
        for (long date : activityDateList) {
            activityRecords.remove(date);
        }

        long firstCgmEntry = cgmRecords.firstKey();
        trackTime = cgmRecords.ceilingKey(firstCgmEntry + 24 * HOUR);

        DataTimer timerTask = new DataTimer ();
        Timer timer = new Timer();
        timer.schedule(timerTask, 15 * SECOND, 15 * SECOND);
    }

    public void parseFile (InputStream stream, SimpleDateFormat format, TreeMap map, boolean isDouble) throws ParseException {
        Scanner scan = new Scanner(stream);
        boolean start = false;
        while (scan.hasNext()) {
            String line = scan.nextLine();
            if (start) {
                Scanner scanComma = new Scanner(line).useDelimiter(",");
                int tokenCount = 0;
                Date date = null;
                double value = 0;
                try {
                    while (scanComma.hasNext()) {
                        String innerLine = scanComma.next();
                        if (tokenCount == 0) {
                            date = format.parse(innerLine);
                        } else if (tokenCount == 1) {
                            value = Double.parseDouble(innerLine);
                        }
                        tokenCount++;
                    }
                    if (isDouble) {
                        map.put(date.getTime(), value);
                    } else {
                        map.put(date.getTime(), (int) value);
                    }
                }
                catch (Exception e) {
                    Log.v("tag", e.getMessage());
                }
            }
            start = true;
        }
    }

    public Map<Long, Double> getCgmRecords (double hoursRange) {
        synchronized (cgmRecords) {
            return getRecords(hoursRange, cgmRecords);
        }
    }

    public Map<Long, Integer> getBolusRecords (double hoursRange) {
        return getRecords(hoursRange, bolusRecords);
    }

    public Map<Long, Integer> getCarbsRecords (double hoursRange) {
        return getRecords(hoursRange, carbRecords);
    }

    public Map<Long, Integer> getActivityRecords (double hoursRange) {
        return getRecords(hoursRange, activityRecords);
    }

    public int getYUpperBound() {
        Collection<Double> coll = cgmRecords.values();
        double highest = 0;
        for (double d : coll) {
            if (d>highest) {
                highest = d;
            }
        }
        return (int)highest + 1;
    };

    public int getYLowerBound() {
        return 0;
    }

    public int getUpperCgmTarget() {
        return 180;
    }

    public int getLowerCgmTarget() {
        return 99;
    }

    public Map getRecords (double hoursRange, TreeMap records) {
        Map newMap;
        long startTime;
        startTime =  getCurrentTime();

        long pastTime = startTime - (long)(hoursRange * HOUR);
        try {
            newMap = records.subMap(pastTime, true, startTime, true);
        }
        catch (Exception e) {
            newMap = null;
        }
        return newMap;
    }

    public double getCgmValue(long key) {
        if (!cgmRecords.isEmpty()) {
            synchronized (cgmRecords) {
                return cgmRecords.get(cgmRecords.floorKey(key));
            }
        }
        else {
            return 0;
        }
    }

    public long getCurrentTime () {
        return trackTime;
    }

    public long getCurrentCgmTime() {
        return trackTime;
    }

    public String getCurrentCarbsValue() {
        if (!carbRecords.isEmpty()) {
            return Integer.toString(carbRecords.get(carbRecords.floorKey(trackTime)));
        }
        else {
            return "0";
        }
    }

    public String getCurrentBolusValue() {
        if (!bolusRecords.isEmpty()) {
            return Integer.toString(bolusRecords.get(bolusRecords.floorKey(trackTime)));
        }
        else {
            return "0";
        }
    }

    public String getCurrentBloodGlucose() {
        if (!cgmRecords.isEmpty()) {
            return Double.toString(cgmRecords.get(cgmRecords.floorKey(trackTime)));
        }
        else {
            return "0";
        }
    }


     private class DataTimer extends TimerTask {
        public void run() {
            try {
                long testTime = trackTime + 5 * MINUTE;
                trackTime = cgmRecords.ceilingKey(testTime);
                updateType.postValue(UpdateType.CGM);
            } catch (Exception e) {
                Log.v("tag", e.getMessage());
            }
        }
    }
}