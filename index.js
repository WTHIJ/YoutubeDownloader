const fs = require('fs');
const readline = require('readline');
const ytdl = require('ytdl-core');
const ProgressBar = require('progress');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.question('Entrez le lien de la vidéo YouTube : ', (videoUrl) => {
  rl.question('Entrez le nom du fichier de sortie (sans extension) : ', (fileName) => {
    const outputFilePath = `${fileName}.mp4`;
    const videoStream = ytdl(videoUrl, { quality: 'highestvideo', filter: 'videoandaudio' });
    const fileSize = fs.statSync(outputFilePath).size;
    const progressBar = new ProgressBar('[:bar] :percent :etas', {
      complete: '=',
      incomplete: ' ',
      width: 20,
      total: fileSize
    });

    videoStream.on('progress', (chunkLength, downloaded, total) => {
      progressBar.tick(chunkLength);
    });

    videoStream.pipe(fs.createWriteStream(outputFilePath))
      .on('finish', () => {
        console.log('\nTéléchargement terminé !');
      })
      .on('error', (error) => {
        console.error('Une erreur est survenue lors du téléchargement :', error);
      });

    rl.close();
  });
});
