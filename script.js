const fs = require('fs');
const readline = require('readline');
const ytdl = require('ytdl-core');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.question('Entrez le lien de la vidéo YouTube : ', (videoUrl) => {
  rl.question('Entrez le nom du fichier de sortie (sans extension) : ', (fileName) => {
    const outputFilePath = `${fileName}.mp4`; 

    const videoStream = ytdl(videoUrl, { quality: 'highestvideo', filter: 'videoandaudio' });
    const fileStream = fs.createWriteStream(outputFilePath);

    let downloadedBytes = 0;
    let totalBytes = 0;

    videoStream.on('response', (response) => {
      totalBytes = parseInt(response.headers['content-length'], 10);
    });

    videoStream.on('data', (chunk) => {
      downloadedBytes += chunk.length;
      const progress = (downloadedBytes / totalBytes) * 100;
      readline.cursorTo(process.stdout, 0);
      process.stdout.write(`Téléchargement en cours... ${progress.toFixed(2)}%`);
    });

    videoStream.pipe(fileStream);

    fileStream.on('finish', () => {
      console.log('\nTéléchargement terminé !');
      rl.close();
    });

    fileStream.on('error', (error) => {
      console.error('\nUne erreur est survenue lors de l\'écriture du fichier :', error);
      rl.close();
    });
  });
});
