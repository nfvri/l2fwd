import flask
import os
import sys
import ast
import json
import requests

app = flask.Flask(__name__)
ip_traffic = ""

@app.route('/stats/<prefix>')
def get_stats(prefix):
    """ Retrieves the last saved stats for the dpdk app with prefix l1
        Args:
            -
        Returns:
            dict: A JSON object containing the stats
    """
    status = 200
    return flask.Response(get_stats_json(prefix),
                          status=status,
                          mimetype='application/json')

def get_stats_json(prefix):
    try:
        f = open('telemetry_stats' + prefix + '.json', 'r')
        line = f.readline()
        while line:
            if "stats" in line:
                str_dict = line.split('>')[1]
                break
            line = f.readline()
        stats_dict = ast.literal_eval(str_dict)

        r = requests.get("http://" + ip_traffic + ":5001/tx_stats")
        traffic_stats_dict = r.json()
        metric = "tx_bps-pgid_" + prefix.split('l')[1]
        if metric in traffic_stats_dict:
            stats_dict["rx_bps"] = traffic_stats_dict[metric]

        js = json.dumps(stats_dict, indent=2)

        return js

    except Exception as e:
        print("An exception occurred")
        print(str(e))

    finally:
        f.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Wrong arguments! Please give the ip to get traffic bps per stream")
        exit(0)

    ip_traffic = sys.argv[1]
    app.run(host='0.0.0.0', port=5000, debug=True)

