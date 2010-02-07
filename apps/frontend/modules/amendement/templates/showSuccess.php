<?php $titre1 = $amendement->getTitre().' ('.preg_replace('/indéfini/i', 'Sort indéfini', $amendement->getSort()).')';
      if ($section) $titre2 = link_to(ucfirst($section->titre), '@section?id='.$section->id);
      else $titre2=""; ?>
<?php $sf_response->setTitle(strip_tags($titre2.'  '.$titre1)); ?>
<div class="amendement" id="L<?php echo $amendement->texteloi_id.$amendement->getLettreLoi(); ?>-A<?php echo $amendement->numero; ?>">
<div class="source"><a href="<?php echo $amendement->source; ?>">source</a> - <a href="<?php echo $amendement->getLinkPDF(); ?>">PDF</a></div>
<h1><?php echo $titre1; ?></h1>
<h2><?php echo $titre2; ?></h2>
<div class="identiques">
  
</div>
<?php if ($seance || count($identiques) > 1) { ?>
<div class="seance_amendements">
  <h3><?php if ($seance) echo 'Discuté en '.link_to('séance le '.myTools::displayDate($seance['date']), '@interventions_seance?seance='.$seance['seance_id'].'#amend_'.$amendement->numero);
  if (count($identiques) > 1) {
    if (count($identiques) > 2)
      $ident_titre = " ( amendements identiques : ";
    else $ident_titre = " ( amendement identique : "; ?>
  <em><?php echo $ident_titre; foreach($identiques as $identique) if ($identique->numero != $amendement->numero)
      echo link_to($identique->numero, '@amendement?id='.$identique->id)." "; ?>)</em>
  <?php } ?></h3>
</div>
<?php } ?>
<?php if ($sous_admts) { ?>
<p>Sous-amendements associés&nbsp: <?php foreach($sous_admts as $sous)
 echo link_to($sous['numero'], '@amendement?id='.$sous['id']).' '; ?></p>
<?php } ?>
<div class="signataires">
  <p>Déposé le <?php echo myTools::displayDate($amendement->date); ?> par : <?php echo $amendement->getSignataires(1); ?>.</p>
  <?php 
  $deputes = $amendement->getParlementaires(); ?>
  <div class="photos"><p>
  <?php $n_auteurs = count($deputes); $line = floor($n_auteurs/(floor($n_auteurs/16)+1)); $ct = 0; foreach ($deputes as $depute) {
    $titre = $depute->nom.', '.$depute->groupe_acronyme;
    if ($ct != 0 && $ct != $n_auteurs-1 && !($ct % $line)) echo '<br/>'; $ct++;
    echo '<a href="'.url_for($depute->getPageLink()).'"><img width="50" height="64" title="'.$titre.'" alt="'.$titre.'" src="'.url_for('@resized_photo_parlementaire?height=70&slug='.$depute->slug).'" /></a>&nbsp;';
  } ?></p></div>
</div>
<div class="sujet">
  <h3><?php $sujet = $amendement->getSujet();
    if ($loi && preg_match('/^(.*)?(article\s*)((\d+|premier).*)$/i', $sujet, $match)) {
      $art = preg_replace('/premier/i', '1er', $match[3]);
      $sujet = $match[1].link_to($match[2].$match[3], '@loi_article?loi='.$loi->texteloi_id.'&article='.$art);
    }
    echo $sujet.' ';
    if ($loi) echo '&mdash; '.link_to(preg_replace('/Simplifions la loi 2\.0 : (.*)\s*<br.*$/', '\1', $loi->titre), '@loi?loi='.$loi->texteloi_id);
    else echo 'de la loi N° '.myTools::getLinkLoi($amendement->texteloi_id).$amendement->getLettreLoi(1); ?></h3>
</div>
<div class="texte_intervention">
  <?php echo $amendement->getTexte(); ?>
</div>
<div class="expose_amendement">
  <h3>Exposé Sommaire :</h3>
  <?php echo $amendement->getExpose(); ?>
</div>
<div class="commentaires" id="commentaires">
<?php if ($amendement->nb_commentaires == 0)
  echo '<h3>Aucun commentaire n\'a encore été formulé sur cet amendement</h3>';
else echo include_component('commentaire', 'showAll', array('object' => $amendement));
echo include_component('commentaire', 'form', array('object' => $amendement)); ?>
</div>
</div>
