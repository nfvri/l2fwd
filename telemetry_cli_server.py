import flask
import os
import sys
import ast
import json

app = flask.Flask(__name__)


@app.route('/dpdk_stats_l1')
def get_dpdk_stats_l1():
    """ Retrieves the last saved dpdk stats for app with prefix l1
        Args:
            -
        Returns:
            dict: A JSON object containing the dpdk stats
    """
    status = 200
    return flask.Response(get_stats_json("l1"),
                          status=status,
                          mimetype='application/json')

@app.route('/dpdk_stats_l2')
def get_dpdk_stats_l2():
    """ Retrieves the last saved dpdk stats for app with prefix l2
        Args:
            -
        Returns:
            dict: A JSON object containing the dpdk stats
    """
    status = 200
    return flask.Response(get_stats_json("l2"),
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
        js = json.dumps(stats_dict, indent=2)
        return js

    except Exception as e:
        print("An exception occurred")
        print(str(e))

    finally:
        f.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

