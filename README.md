# Tai-ShengYeh.github.io
<!DOCTYPE html>
<html lang="en">
<head>
<title>Show/Hide image with jQuery</title>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
<script type="text/javascript">
$(document).ready(function(){
	$('#btn1').click(function(){
   		$('#imgDiv').show();
	});
  	$('#btn2').click(function(){
   		$('#imgDiv').hide();
	});
});
</script>
</head>
<body>
<div id="imgDiv">
	<img src="/uploads/317641.jpg" alt="Show/Hide Image" />
</div>
<button type="button" id="btn1">Show</button>
<button type="button" id="btn2">Hide</button>
</body>
</html>
