from flask import Blueprint
from flask import Flask, render_template, request, redirect, url_for, send_file, flash

#from api.compute import compute

import uuid
import json
import os
import re
import shutil
import subprocess
import configparser
import pandas as pd
import numpy as np
import csv

personal = Blueprint('personal', __name__, template_folder='templates')

solventes = {"methanol": "Methanol-D4 (CD3OD)",
             "chloroform": "Chloroform-D1 (CDCl3)"}

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

def xlsx2spectrum(src, uid):
    peaks = pd.read_excel(src)

    f = open('api/static/results/%s/realspectrum.csv' %uid, 'w')
    hsqc = peaks[['f1 (ppm)',  'f2 (ppm)']]
    hsqc = hsqc[~hsqc['f1 (ppm)'].isna()]
    f.write('HSQC\n')
    for i in hsqc.index:
        f.write('{}\t{}\n'.format(*hsqc.loc[i]))

    hmbc = peaks[['f1 (ppm).1',  'f2 (ppm).1']]
    hmbc = hmbc[~hmbc['f1 (ppm).1'].isna()]
    f.write('HMBC\n')
    for i in hmbc.index:
        f.write('{}\t{}\n'.format(*hmbc.loc[i]))

    f.close()

@personal.route('/')
def index():
    return render_template('home.html')

@personal.route('/graph')
def graph():
    df = pd.read_csv('Advertising.csv', index_col=0)
    df.sort_values(['Sales'], inplace=True)
    fig = go.Figure()
    for cname in df.columns[:-1]:
        fig.add_scatter(x=df[cname], y=df['Sales'], name=cname, mode="markers")

    fig.update_layout(width=1600, height=800)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('graph.html',
                           ids='invest',
                           graphJSON=graphJSON)

@personal.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        filename = f'{str(uuid.uuid4())}_{f.filename}'
        f.save(os.path.join('api/static/uploads', filename))
    return render_template('upload.html')

@personal.route('/analysis', methods=['POST', 'GET'])
def analysis():
    options = os.listdir('api/static/uploads')
    error = None
    if request.method == 'POST':
        form_dict = dict(request.form)
        #data_list = request.form.getlist('category')
        #data_list = request.form.getlist('isselect_code')
        peaks = request.form.getlist('isselect_code')
        molecules = request.form.getlist('isselect_code1')

        solvente = solventes[form_dict['analise']]
        if form_dict['remove']=='sim':
            data_list = peaks+molecules
            if len(data_list):
                for fn in data_list:
                    os.remove(os.path.join('api/static/uploads', fn))
            return redirect(url_for('personal.analysis'))
        try:
            uid = str(uuid.uuid4())
            res = 'api/static/results/%s' % uid
            #Criar um diretório dentro do diretório 'results'
            os.mkdir(res)
            if len(peaks)==1:
                src = os.path.join('api/static/uploads', peaks[0])
                dst = os.path.join('api/static/results', uid, peaks[0].split('_')[1])
                xlsx2spectrum(src,uid)
            if len(molecules)==1:
                src = os.path.join('api/static/uploads', molecules[0])
                mol = pd.read_csv(src)
                df = pd.DataFrame(mol)
                df['SMILES'].to_csv('api/static/results/%s/testall.smi' %uid, header=None, index=None)
                df['compound NAME'].to_csv('api/static/results/%s/testallnames.txt' %uid, header=None, index=None)

            config = configparser.RawConfigParser()
            config.read('nmrproc.properties')
            config['onesectiononly']['solvent'] = solvente
            with open('api/nmrproc.properties', 'w+') as f:
                config.write(f)
            res = 'static/results/%s' % uid
            subprocess.call(['python', 'api/nmrfilter_reshape.py',
                             res, '>&', os.path.join(res, 'log.txt')])



        except Exception as e:
            #print(e)
            return render_template('analysis.html', options=options,
                                   error=str(e))
        return redirect(url_for('personal.results'))
    return render_template('analysis.html', options=options, error=error)


@personal.route('/results')
def results():
    fls = os.listdir('api/static/results')
    meas = []
    for fl in fls:
        meas.append([fl, '/static/results/%s' % fl])
    ddffinal = json.dumps(meas, cls=NpEncoder)
    return render_template('results.html',
                           dffinal=ddffinal)


@personal.route('/download')
def download():
    taskid = request.args.get('taskid')
    filename = request.args.get('filename')
    ty = request.args.get('ty')
    fls = f'static/results/{taskid}/{ty}/{filename}'
    return send_file(fls, as_attachment=True)

@personal.route('/listfiles')
def listfiles():
    taskid = request.args.get('taskid')
    ty = request.args.get('ty')
    fls = os.listdir(f'api/static/results/{taskid}/{ty}')
    #filelist = json.dumps(fls, cls=NpEncoder)
    return render_template('filelist.html', filelist=fls,
                           tkid=taskid, ty=ty)

@personal.route('/delete')
def delete():
    taskid = request.args.get('taskid')
    dr = os.path.join('api/static/results')
    fls = os.listdir(dr)
    fls = [x for x in fls if taskid in x][0]
    fls = 'api/static/results/%s' % fls
    if os.path.isfile(fls):
        os.unlink(fls)
    else:
        shutil.rmtree(fls)
    return redirect(url_for('personal.results'))

