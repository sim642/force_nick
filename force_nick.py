import weechat
import sys
import re

weechat.register("force_nick", "sim642", "0.1", "TODO", "Force nick change on channels which disallow it", "", "")
#weechat.prnt("", "Hi, this is script")
#weechat.prnt("", str(sys.version_info))

servers = {}

def parse_message(signal_data):
	hashtable = weechat.info_get_hashtable("irc_message_parse", {"message": signal_data})

	# parse arguments string into usable pieces
	args = hashtable["arguments"].split(":", 1)
	hashtable["args"] = args[0].split()
	if len(args) > 1:
		hashtable["text"] = args[1]

	return hashtable

def channel_block(server, channel):
	#global servers

	#weechat.prnt("", "nickblock: %s,%s" % (server, channel))

	servers[server]["channels"].append(channel)
	weechat.hook_signal_send("irc_input_send", weechat.WEECHAT_HOOK_SIGNAL_STRING, "%s;;1;;/part %s" % (server, channel))
	weechat.hook_signal_send("irc_input_send", weechat.WEECHAT_HOOK_SIGNAL_STRING, "%s;;1;;/nick %s" % (server, servers[server]["nick"]))

def nick_out_cb(data, signal, signal_data):
	#global servers

	server = signal.split(",")[0]
	parsed = parse_message(signal_data)
	nick = parsed["args"][0]

	if server not in servers: # initialize new nickchange
		servers[server] = {}
		servers[server]["channels"] = []
	
	servers[server]["nick"] = nick

	return weechat.WEECHAT_RC_OK

def nick_in_cb(data, signal, signal_data):
	server = signal.split(",")[0]
	parsed = parse_message(signal_data)
	mynick = weechat.info_get("irc_nick", server)

	#weechat.prnt("", "nick_in: %s" % parsed)

	if parsed["nick"] == mynick: # nick change worked
		for channel in servers[server]["channels"]:
			weechat.hook_signal_send("irc_input_send", weechat.WEECHAT_HOOK_SIGNAL_STRING, "%s;;1;;/join -noswitch %s" % (server, channel))

		servers.pop(server)

	return weechat.WEECHAT_RC_OK

def unreal_cb(data, signal, signal_data):
	server = signal.split(",")[0]
	parsed = parse_message(signal_data)

	match = re.match(r"Can not change nickname while on (#\w+) \(\+N\)", parsed["text"])
	if match:
		channel = match.group(1)
		channel_block(server, channel)

	return weechat.WEECHAT_RC_OK

def freenode_cb(data, signal, signal_data):
	server = signal.split(",")[0]
	parsed = parse_message(signal_data)

	channel_block(server, parsed["args"][2])

	return weechat.WEECHAT_RC_OK

weechat.hook_signal("*,irc_out1_nick", "nick_out_cb", "")
weechat.hook_signal("*,irc_in_nick", "nick_in_cb", "")
weechat.hook_signal("*,irc_in_447", "unreal_cb", "")
weechat.hook_signal("*,irc_in_435", "freenode_cb", "")
