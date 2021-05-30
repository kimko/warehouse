from datetime import timedelta, datetime as dt
from operator import itemgetter

input = """ID  Name        Activity    Time in     Time out
1   Joe         Picking     9:05 AM     9:10 AM      26
2   Joe         Picking     9:15 AM     10:00 AM     26
3   William     Packing     9:15 AM     10:00 AM     27
4   Joe         Packing     11:00 AM    11:45 AM     28
5   Lucy        Packing     11:30 AM    12:20 PM      5
6   Joe         Picking     11:50 AM    12:30 PM     29
7   William     Packing     10:30 AM    1:00 PM       
8   Lucy        Picking     12:25 PM    1:00 PM      32
9   Lucy        Cleaning    1:00 PM     1:05 PM      32
10  Lucy        Picking     1:05 PM     2:00 PM      32
11  William     Packing     1:30 PM     3:00 PM      
12  William     Picking     3:05 PM     5:00 PM      33
13  Joe         Cleaning    11:55 PM    12:35 AM"""



output = """Name    Activity    Start Time  End Time
Joe     Picking     9:05 AM     10:00 AM (0)
William Packing     9:15 AM     10:00 AM (6)
Joe     Packing     11:00 AM    11:45 AM (1)
Joe     Picking     11:50 AM    12:30 PM (2)
Lucy    Packing     11:30 AM    12:20 PM (4)
William Packing     10:30 AM    3:00 PM (7)
Lucy    Picking     12:25 PM    2:00 PM (5)
William Picking     3:05 PM     5:00 PM (9)"""


# read raw data
rows = [row.split() for row in input.split("\n")]
data = [
    {
        "ID": row[0],
        "Name": row[1],
        "Activity": row[2],
        "Time in": dt.strptime(f"{row[3]} {row[4]}", "%I:%M %p"),
        "Time out": dt.strptime(f"{row[5]} {row[6]}", "%I:%M %p"),
    }
    for row in rows[1:]
]

# sort data, add duration and adjust for "midnight shift"
data = sorted(data, key=itemgetter("Name", "Time in"))
_ = [
    row.update({"Time out": row["Time out"] + timedelta(hours=24)})
    for row in data
    if row["Time out"] < row["Time in"]
]
_ = [row.update({"Duration": row["Time out"] - row["Time in"]}) for row in data]

outputData = []
outputRow = {}
activity = ""
name = ""
startTime = ""
timeOut = ""
append = False
NOON = dt(1900, 1, 1, 12, 0)
TWOPM = dt(1900, 1, 1, 14, 0)

for row in data:
    if name != row["Name"]:
        if name:
            append = True
        name = row["Name"]

    if activity != row["Activity"]:
        if activity and row["Duration"] > timedelta(minutes=5):
            append = True
            activity = row["Activity"]
        if activity == "":
            activity = row["Activity"]

    # we allow 5 minute time gaps (IE ID 1 + 2)
    if timeOut and row["Time in"] - timeOut > timedelta(minutes=5):
        # we allow 30 minute breaks between 12:00 and 14:00
        if (row["Time in"] - timeOut) >= timedelta(minutes=5) and (
            (timeOut < NOON) or (row["Time in"] > TWOPM)
        ):
            append = True

    if append:
        outputRow["End Time"] = timeOut
        outputRow["Duration"] = outputRow["End Time"] - outputRow["Start Time"]
        outputData.append(outputRow)
        print("WRITE", outputRow)
        outputRow = {}
        append = False
        startTime = ""

    if startTime == "":
        startTime = row["Time in"]
    outputRow["Start Time"] = startTime
    outputRow["Name"] = row["Name"]
    outputRow["Activity"] = activity
    timeOut = row["Time out"]

if outputRow:
    outputRow["End Time"] = timeOut
    outputRow["Duration"] = outputRow["End Time"] - outputRow["Start Time"]
    outputData.append(outputRow)


import pandas as pd
df = pd.DataFrame(outputData)
df = df[["Name", "Activity", "Start Time", "End Time", "Duration"]]


"""
    (A)
    Inconsitency in the expected output.
    ID 13 is not accounted. Joe perfomred activity "cleaning"
    from 11:55 PM to 12:35 AM

    (B)
    I noticed that ID 7 and 11 goot aggregaged. 
    I assume a half hour lunch time was allowed and that lunch is time fenced between 12:00 and 2 PM
    (other wise ID 3 would have been aggreageted as well)
        3   William     Packing     9:15 AM     10:00 AM
        7   William     Packing     10:30 AM    1:00 PM 
        11  William     Packing     1:30 PM     3:00 PM 

"""
