<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Upload Photo</title>
    <link rel="icon" href="data:,">

    <!-- API Gateway SDK dependencies -->
    <script src="sdk/lib/axios/dist/axios.standalone.js"></script>
    <script src="sdk/lib/CryptoJS/rollups/crypto-js.js"></script>
    <script src="sdk/lib/CryptoJS/rollups/sha256.js"></script>
    <script src="sdk/lib/CryptoJS/components/hmac.js"></script>
    <script src="sdk/lib/CryptoJS/components/enc-base64.js"></script>
    <script src="sdk/lib/url-template/url-template.js"></script>
    <script src="sdk/lib/apiGatewayCore/sigV4Client.js"></script>
    <script src="sdk/lib/apiGatewayCore/apiGatewayClient.js"></script>
    <script src="sdk/lib/apiGatewayCore/simpleHttpClient.js"></script>
    <script src="sdk/lib/apiGatewayCore/utils.js"></script>
    <script src="sdk/apigClient.js"></script>

    <style>
        body {
            font-family: Arial;
            margin: 40px;
            background: #f4f4f4;
        }
        .nav a {
            padding: 10px 20px;
            background: #0073bb;
            color: white;
            text-decoration: none;
            border-radius: 6px;
        }
    </style>
</head>

<body>

<div class="nav">
    <a href="index.html">Back to Search</a>
</div>

<h1>Upload Photo</h1>

<input type="file" id="photoFile"><br><br>
<input type="text" id="customLabels" placeholder="Sam, Sally"><br><br>

<button onclick="uploadPhoto()">Upload</button>

<div id="status"></div>

<script>
    var apigClient = apigClientFactory.newClient({
        apiKey: "1anI1JHNZtaFEwxoG8UEn7exdCvdsRT02NljyLuq"
    });

    function uploadPhoto() {
        let file = document.getElementById("photoFile").files[0];
        let labels = document.getElementById("customLabels").value;

        if (!file) {
            alert("Please select a file.");
            return;
        }

        // FIX: wrap file in Blob so API Gateway gets binary
        let fileBlob = new Blob([file], { type: file.type });

        let params = {
            object: file.name,
            "Content-Type": file.type,
            "x-amz-meta-customLabels": labels
        };

        let additionalParams = {
            headers: {
                "Content-Type": file.type,
                "x-amz-meta-customLabels": labels
            }
        };

        apigClient.uploadPut(params, fileBlob, additionalParams)
            .then(function(response) {
                console.log("Upload success:", response);
                document.getElementById("status").innerHTML =
                    "<b style='color:green;'>Upload Successful!</b>";
            })
            .catch(function(error) {
                console.error("Upload error:", error);
                document.getElementById("status").innerHTML =
                    "<b style='color:red;'>Upload Failed</b>";
            });
    }
</script>

</body>
</html>
