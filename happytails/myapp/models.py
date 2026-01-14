from django.db import models
from django.contrib.auth.models import User 

# Model existent
class Animal(models.Model):
    ANIMAL_SIZES = (
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
    )
    
    ADOPTION_STATUSES = (
        ("AV", "Disponibil"),   
        ("PD", "În proces"),      
        ("AD", "Adoptat"), 
    )

    name = models.CharField(max_length=200)
    breed = models.CharField(max_length=300)
    age = models.CharField(max_length=100)
    size = models.CharField(max_length=1, choices=ANIMAL_SIZES)
    story = models.CharField(max_length=500)
    image = models.ImageField(upload_to='animals/', blank=True, null=True)
    status = models.CharField(
        max_length=2,
        choices=ADOPTION_STATUSES,
        default="AV"
    )
    favorites = models.ManyToManyField(User, related_name='favorite_animals', blank=True)


class Adoption(models.Model):
    STATUS_CHOICES = (
        ('PD', 'Pending'),
        ('AP', 'Approved'),
        ('RJ', 'Rejected'),
        ('FN', 'Finalized'),
        ('CN', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='adoptions')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='adoption_applications')
    
    # application details
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='PD')
    
    # adoption application info
    phone = models.CharField(max_length=20)
    address = models.TextField()
    reason = models.TextField(help_text="De ce vrei să adopți acest animal?")
    experience = models.TextField(help_text="Ai experiență cu animale?")
    living_situation = models.CharField(max_length=200, help_text="Casă/Apartament, Curte, etc.")
    
    # visit
    visit_scheduled = models.BooleanField(default=False)
    visit_date = models.DateTimeField(null=True, blank=True)
    visit_notes = models.TextField(blank=True)
    
    # review admin
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_adoptions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # finalize
    finalized_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.animal.name} ({self.get_status_display()})"
    


class Visit(models.Model):
    STATUS_CHOICES = (
        ('SC', 'Scheduled'),
        ('CF', 'Confirmed'), 
        ('CM', 'Completed'),
        ('CN', 'Cancelled'),
    )

    adoption = models.ForeignKey(Adoption, on_delete=models.CASCADE, related_name='visits')
    volunteer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='volunteer_visits')
    
    # schedule
    scheduled_date = models.DateTimeField()
    scheduled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='scheduled_visits')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # status
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='SC')
    confirmed_at = models.DateTimeField(null=True, blank=True)

    # report post-visit
    completed_at = models.DateTimeField(null=True, blank=True)
    report = models.TextField(blank=True, help_text="Raport despre cum a decurs vizita")
    animal_behavior = models.TextField(blank=True, help_text="Comportamentul animalului")
    client_interaction = models.TextField(blank=True, help_text="Interacțiunea cu clientul")
    recommendation = models.CharField(
        max_length=2,
        choices=(
            ('AP', 'Approve'),
            ('RJ', 'Reject'),
            ('PD', 'Pending'),
        ),
        blank=True
    )
    
    # notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Visit {self.id} - {self.adoption.animal.name} ({self.get_status_display()})"