from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse
# Create your views here.
from django.shortcuts import render
from AIG.models import AIG
from AIG.forms import AIGForm
import matplotlib
from datetime import datetime
from django.utils import timezone
import time
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import urllib, base64
import pandas as pd
import json
from fbprophet import Prophet
from sklearn.metrics import mean_squared_error


def home(request):
        check="123"
        if request.method == 'POST':
                form = AIGForm(request.POST)
                check = form.is_valid()
                #if form.is_valid():
                users = request.POST.get('users','')
                bandwidth = request.POST.get('bandwidth','')
                decision = request.POST.get('currentBandwidth','')
                choice = request.POST.get('method','')
                if(choice=="1"):
                        method=1
                elif(choice=="2"):
                        method=2
                if (decision=="nochange"):
                        event=AIG.objects.last()
                        eventmarking = getattr(event,'eventmarking')
                else:
                        eventmarking= request.POST.get('network','')
                dateOBJ = datetime.now()
                _now = dateOBJ.strftime('%Y/%m/%d')
                aig_obj = AIG(users=users, bandwidth=bandwidth, eventmarking=eventmarking, eventtimestamp=_now)
                #aig_obj = AIG(users=users, bandwidth=bandwidth, eventmarking='500')
                aig_obj.save()
        else:
                form = AIGForm()
                _now = datetime.now().strftime("%Y-%m-%d")
                method=1
        data2 = pd.read_excel('data1projandusers.xlsx',sheet_name=0,keep_default_na=True)
        #Setting the data with only the 4 variables
        data2 = data2[['MonthYear','PercentInBH','InBandwidth','ProjectNo','UserNo']]
        #data2 = data2[0:-6]#this line prevents the dcode to neglect some of the initial data
        #some_data = (data2.iloc[:,1]*data2.iloc[:,2])/(8500*data2.iloc[:,4])
        #print(some_data)
        #data2['ds'] = data2['MonthYear']
        #remove the NAN values from the dataset
        data2 = data2.dropna()
        #Reverse the data
        data2 = data2.iloc[::-1]
        data2 = data2.reset_index()
        userdata = data2[['InBandwidth','ProjectNo','UserNo']]
        data2.rename(columns={'MonthYear':'ds','PercentInBH':'y'},inplace=True)
        test_data = data2[['y']].tail(3)
        data2 = data2[0:-3]#this line makes the code to avoid taking the last 3 rows of data
        if (method==2):
                userdata = userdata.iloc[::-1]
                userdata = userdata.reset_index()
                lastdata = AIG.objects.last()
                last = getattr(lastdata,'eventtimestamp')
                userdata.iloc[0,1:4] = [getattr(lastdata,'eventmarking'),getattr(lastdata,'bandwidth'),getattr(lastdata,'users')]
                userdata.iloc[1,1:4] = [getattr(lastdata,'eventmarking'),getattr(lastdata,'bandwidth'),getattr(lastdata,'users')]
                userdata.iloc[2,1:4] = [getattr(lastdata,'eventmarking'),getattr(lastdata,'bandwidth'),getattr(lastdata,'users')]
                userdata = userdata.iloc[::-1]
                userdata = userdata.reset_index()
                print("The new variable data is being used")
        else:
                print("The excel data is bein used")
        print(data2)
        print(userdata)
        model = Prophet(weekly_seasonality=True, daily_seasonality=False,yearly_seasonality=False,interval_width=0.95)
        model.add_regressor('UserNo')
        model.add_regressor('ProjectNo')
        model.add_regressor('InBandwidth')
        model.fit(data2)
        future_dates = model.make_future_dataframe(periods=3,freq='MS',include_history=True)
        future_dates[['InBandwidth','ProjectNo','UserNo']] = userdata[['InBandwidth','ProjectNo','UserNo']]
        future_dates = future_dates.dropna()
        prediction = model.predict(future_dates)
        prediction[['ds', 'yhat', 'yhat_lower', 'yhat_upper','ProjectNo','UserNo']].tail(3)
        result = prediction[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(3)
        result_data = result[['yhat_lower']]
        mean_sq_error = mean_squared_error(test_data,result_data, squared=False)
        print(result)
        data_set = result.to_json(orient='split')
        print(json.dumps(data_set))
        data_set = json.dumps(data_set)
        plot = model.plot(prediction)
        print(result.iloc[0,:])
        status = result.iloc[0,1]
        if status>95:
            status="The network bandwidth needs to be upgraded"
        elif status<30:
            status="The network bandwidth is underutilized reduce the bandwidth"
        else:
            status = "The network bandwidth capacity is accurate"
        buf1 = io.BytesIO()
        plot.savefig(buf1,format='png')
        buf1.seek(0)
        string1 = base64.b64encode(buf1.read())
        uri1 = urllib.parse.quote(string1)
        data =AIG.objects.all()
        firstdata = AIG.objects.first()
        first = getattr(firstdata,'eventtimestamp')
        print(first)
        print(getattr(firstdata,'users'))
        lastdata = AIG.objects.last()
        last = getattr(lastdata,'eventtimestamp')
        print(last)
        da = {
        "aig_details":data
        }
        return render(request,'home.html', {
        'form':form,
        'aig_details':data,
        'plot':uri1,
        'eventmarking':"Increase bandwidth",
        'count':data.count(),
        'check':check,
        'now':_now,
        'last':last,
        'lastdata':lastdata,
        'first':first,
        'result':data_set,
        'status' : status,
        'mean_error':mean_sq_error,
        })
