<html>
<head>
  <title>Bastelzimmer Power Management</title>
  <meta http-equiv="refresh" content="10" />
</head>
<body>

<p>Available Outlets:</p>
<table border="1" width="50%">
  <tr>
    <th>Outlet</th>
    <th>Status</th>
    <th>Switch on</th>
    <th>Switch off</th>
  </tr>
%for outlet in outlets:
  <tr>
    <td>{{outlet}}</td>
    <td>{{status[outlet]}}</td>
    <td><a href="/switch_show_status/{{outlet}}/on">On</a></td>
    <td><a href="/switch_show_status/{{outlet}}/off">Off</a></td>
  </tr>
%end
</table>


</body>
</html>