  <div class="intervention" id="<?php echo $intervention->id; ?>">
    <div class="info">
    <strong>  
    <?php 
    echo $intervention->getSeance()->getDate().' : ';
    
    if ($intervention->getType() == 'commission') { echo $intervention->getSeance()->getOrganisme()->getNom(); }
    else { echo $intervention->getSection()->getTitreComplet(); }
    ?> 
    </strong>
    <span class="source">
      <a href="<?php echo url_for('@interventions_seance?seance='.$intervention->getSeance()->id); ?>#inter_<?php echo $intervention->getMd5(); ?>">Voir l'intervention dans son contexte</a>
    </span>
    </div>
    <div class="texte_intervention"><?php 
$inter = $intervention->getIntervention(); 
if (isset($highlight))
  foreach ($highlight as $h) {
    $inter = preg_replace('/([^\wéè]|^)('.$h.'[es]*)([^\wéè]|$)/i', '\\1<b>\\2</b>\\3', $inter);
  }
echo $inter;
?></div>
    <div class="commentaires">
      3 commentaires dont celui de toto :
      Cette intervention c'est de la balle !
    </div>
  </div>
