# Tai-ShengYeh.github.io
<!DOCTYPE html>
<html>
<head>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script> 
$(document).ready(function(){
  $("#flip").click(function(){
  $("#panel").slideDown("slow");
  });

  $(".tog").click(function(){
  $('img',this).toggle();
  });

  });
</script>
<style> 
#panel, #flip {
  padding: 5px;
  text-align: center;
  background-color: #e5eecc;
  border: solid 1px #c3c3c3;
}

#panel {
  padding: 50px;
  display: none;
}
</style>
</head>

<body>
 
<div id="flip">關於我</div>
<div id="panel">應美臨心雙主修!</div>

<span class="tog">
   <img src="317623.jpg">
   <img src="317626.jpg" style="display:none;">
</span>


</body>
</html>
