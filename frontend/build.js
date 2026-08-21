delete process.env.WIN_CSC_LINK;
delete process.env.CSC_LINK;
delete process.env.CSC_KEY_PASSWORD;
process.env.CSC_IDENTITY_AUTO_DISCOVERY = 'false';

const builder = require('electron-builder');
const Platform = builder.Platform;

builder.build({
  targets: Platform.WINDOWS.createTarget(['portable'], builder.Arch.x64),
  config: {
    appId: 'com.jawahar.storemanager',
    productName: 'Jawahar Enterprises',
    directories: {
      output: 'dist'
    },
    files: [
      'main.js',
      'loading.html',
      'templates/**/*',
      'static/**/*'
    ],
    win: {
      target: [
        {
          target: 'portable',
          arch: ['x64']
        }
      ],
      icon: 'static/images/icon-512.png',
      certificateFile: null,
      cscLink: null,
      verifyUpdateCodeSignature: false,
      sign: async () => {}
    },
    portable: {
      artifactName: '${productName} ${version} Portable.exe',
      useZip: false
    },
    extraResources: [
      {
        from: '../backend/dist/backend.exe',
        to: 'backend.exe'
      }
    ]
  }
}).then((result) => {
  console.log('Build completed successfully! Artifacts:', result);
}).catch((error) => {
  console.error('Build failed:', error);
  process.exit(1);
});
