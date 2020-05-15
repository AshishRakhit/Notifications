from ciphercommon.config import CipherConfig
from processinsights.ProcessAPI import createapp

app = createapp()

if __name__ == '__main__':
    
    #app.run(debug=True)

    config = CipherConfig.load('parameters.yaml')
    websettings = config['WebServer']
    app.run(host='0.0.0.0', port=websettings['Port'])



