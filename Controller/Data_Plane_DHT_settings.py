


highly_verbose=0
verbose=1
generate_topo_json=1
RING_SIZE=6 # this must also be changed in the P4 file and the servers (if you are to change it)
"""
Connections in mininet are bidirectional, so should be for minient 1
if not should be 0
"""
bidirectional_connections=1
log_file="../logs/"
test=1

Rewrite_implementation=1


class settingsError(Exception):
	"""This error is raised if a function is not complient with a certain setting"""
	pass
