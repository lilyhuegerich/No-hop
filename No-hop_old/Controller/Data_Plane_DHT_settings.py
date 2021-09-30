
highly_verbose=0 #: very detailed output, especially usefull for debugging
verbose=1  #: standard output
generate_topo_json=1 #: 1 to save generated topology to json, json is rewritten everytime that program is called if set to 1
RING_SIZE=6 #: this must also be changed in the P4 file and the servers (if you are to change it)


bidirectional_connections=1 #:Connections in mininet are bidirectional, so should be for minient 1 if not should be 0

log_file="../logs/" #: where should logs be saved
test=1

Rewrite_implementation=1 #: 1 for No_hop rewrite 0 for No_hop finger table implementation


class settingsError(Exception):
	"""This error is raised if a function is not complient with a certain setting"""
	pass
