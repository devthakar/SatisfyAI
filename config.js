const config = {
    server: 'localhost', // or your IP if remote
    authentication: {
      type: 'default',
      options: {
        userName: 'sa', // replace with your username
        password: 'tolzit87!' // replace with your password
      }
    },
    options: {
      database: 'SatisfyAIDB', // replace with your database name
      encrypt: true,
      trustServerCertificate: true // for development purposes
    }
  };
  