from flask import Flask, request, jsonify
import os
import json
import logging
from cts_envipath import CTSEnvipath


ctsenvipath = CTSEnvipath()


app = Flask(__name__)
app.config.update(
	DEBUG=True
)

# PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
# os.environ.update({
# 	'PROJECT_ROOT': PROJECT_ROOT
# })
logging.basicConfig(level=logging.DEBUG)

###################
# FLASK ENDPOINTS #
###################

@app.route("/envipath")
def test_page():
	pass

@app.route("/envipath/test")
def test_envipath():
	return jsonify({"status": "cts-envipath up and running."})

@app.route("/envipath/rest")
def rest_endpoints():
	pass

@app.route("/envipath/rest/run", methods=["POST"])
def run_envipath():
	"""
	Runs cts_envipath.py module for envipath predictions.
	Calls their external API and polls status to get results.
	"""
	post_dict = request.get_json()
	logging.warning("POST: {}".format(post_dict))
	smiles = post_dict["smiles"]
	
	# TODO: Use gen_limit to determine setting_id:
	gen_limit = post_dict.get("gen_limit", 1)
	setting_id = 'cts-d1-n16'

	tree_dict = ctsenvipath.get_envipath_tree(smiles, setting_id)

	return jsonify({"status": True, "data": json.loads(tree_dict)})

if __name__ == "__main__":
	app.run(debug=True, port=5003)