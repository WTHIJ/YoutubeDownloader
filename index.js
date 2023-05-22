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

    ytdl(videoUrl, { quality: 'highestvideo', filter: 'videoandaudio' })
      .pipe(fs.createWriteStream(outputFilePath))
      .on('finish', () => {
        console.log('Téléchargement terminé !');
      })
      .on('error', (error) => {
        console.error('Une erreur est survenue lors du téléchargement :', error);
      });

    rl.close();
  });
});
