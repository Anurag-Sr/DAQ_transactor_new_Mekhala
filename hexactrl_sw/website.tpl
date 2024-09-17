<!DOCTYPE html>
<html>
<head>
  <title>HexaController {{name}} control</title>
  <script type="text/javascript">
    var wsock = new WebSocket("ws://{{ip}}:8080/websocket");
    var log_sel = ['rocchar', 'trophy', 'sc', 'fc'];

    function CircularArray(maxLength) { this.maxLength = maxLength; }
    CircularArray.prototype = Object.create(Array.prototype);
    CircularArray.prototype.push = function(element) {
    	Array.prototype.push.call(this, element);
    	while (this.length > this.maxLength) { this.shift(); } 
    };

    var logs = new CircularArray(100); 

    wsock.onmessage = function (event) {
    	var msg = event.data.split('++');

    	if (msg[0] == 'DATA') {
		logs.push(msg[1]);
		var textbox = document.getElementById('log');
		textbox.value = '';
		for (var i=0; i < logs.length; i++) { textbox.value += line_select(logs[i]); }
		textbox.scrollTop = textbox.scrollHeight;
		textbox = undefined; /* free var */
    	} else if (msg[0] == 'STATE') {
    		var state = msg[1].split(':');
    		/*console.log(state);*/
    		if (state[0] == 'sc' || state[0] == 'fc') {update_state(state[0], state[1]); }
    	}
	msg = undefined;
    };

    function send(id) { wsock.send(id); }

    function send2() {
	var msg = document.querySelectorAll('input[type=radio]:checked')[0];
    	send(msg.value);
	msg = undefined;
    }

    function update_state(name, state) {
	var btn = document.getElementById(name);
	var dot = document.getElementById(name + '_stat');
	if (state == 'UP') {
		btn.textContent = 'Stop';
		dot.style.backgroundColor = 'green';
	} else if (state == 'DOWN') {
		btn.textContent = 'Start';
		dot.style.backgroundColor = 'red';
	}
	btn = undefined;
	dot = undefined;
    }

    function line_select(line) {
        var name = line.split(':')[0];
        return log_sel.includes(name) ? line : '';
    };

    function clear_log() {
        document.getElementById('log').value = '';
    };

    function select_log() {
        var checkboxes = document.querySelectorAll('input[type=checkbox]:checked');
        var textbox = document.getElementById('log');
        log_sel = []
        clear_log();

        for (var i = 0; i < checkboxes.length; i++) { 
            var checkbox_name = checkboxes[i].value;
            if (checkbox_name == 'fpga') {
                log_sel.push('rocchar');
                log_sel.push('trophy');
            } else {
                log_sel.push(checkbox_name); 
            }
        }
        for (var i = 0; i < logs.length; i++) { 
            textbox.value += line_select(logs[i]); 
        }
	checkboxes = undefined;
	textbox = undefined;
	log_sel = undefined;
    };


  </script>
  <style>
  	.dot {
  		height: 25px;
  		width: 25px;
  		background-color: red;
  		border-radius: 50%;
  		display: inline-block;
  	}
  </style>

</head>
	<body>
        <p>Actions to do on HexaController:</p>
	    <table border='0'>
	    <th> FPGA controls </th>
	    <tr>
	        <form>
	        <td> <input type='radio' name='plt_sel' id='sing' value='rocchar'><label for='sing'>rocchar</label> </td>
	        <td> <input type='radio' name='plt_sel' id='mult' value='trophy'><label for='mult'>trophy</label> </td>
	        </form>
        </tr>
        <tr>
            <td colspan='2' style='text-align:center;'> <button onclick='send2()'>Load FPGA</button> </td>
        </tr>
        </table>
	    <table border='0'>
            <th> Server controls </th>
            <tr>
                <td> Fast control </td>
                <td> <button id='fc' onclick='send(this.id)'>Start</button> </td>
                <td> <span id='fc_stat' class='dot'></span> </td>
            </tr>
            <tr>
                <td> Slow control </td>
                <td> <button id='sc' onclick='send(this.id)'>Start</button> </td>
                <td> <span id='sc_stat' class='dot'></span> </td>
            </tr>
        </table>
        <textarea readonly id="log" cols='125' rows='25'></textarea>
        <table>
            <tr>
                <td> <button onclick='clear_log()'>Clear log</button> </td>
                <form>
                <td> <input type="checkbox" name="resel" value="fpga" checked onclick="select_log()"> FPGA </td>
                <td> <input type="checkbox" name="resel" value="sc" checked onclick="select_log()"> SC </td>
                <td> <input type="checkbox" name="resel" value="fc" checked onclick="select_log()"> FC </td>
                </form>
            </tr>
        </table>
	</body>
</html>
