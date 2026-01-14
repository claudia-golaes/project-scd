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
    

class Activity(models.Model):
    ACTIVITY_TYPES = (
        ('WLK', 'Walk'),
        ('FED', 'Feed'),
        ('CLN', 'Cleaning'),
        ('BTH', 'Bath'),
        ('MED', 'Medication'),
        ('PLY', 'Play time'),
        ('TRN', 'Training'),
        ('OTH', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('PD', 'Pending'),
        ('AS', 'Assigned'),
        ('IP', 'In Progress'),
        ('CM', 'Completed'),
        ('CN', 'Cancelled'),
        ('OV', 'Overdue'),
    )
    
    PRIORITY_CHOICES = (
        ('LW', 'Low'),
        ('MD', 'Medium'),
        ('HG', 'High'),
        ('UR', 'Urgent'),
    )
    
    # info 
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=3, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # schedule
    scheduled_time = models.DateTimeField()
    deadline = models.DateTimeField(help_text="Până când trebuie completată")
    duration_minutes = models.IntegerField(default=30, help_text="Duration in minutes")
    
    # status & priority
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='PD')
    priority = models.CharField(max_length=2, choices=PRIORITY_CHOICES, default='MD')
    
    # assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_activities'
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    # completion
    completed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='completed_activities'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    
    # created info
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_activities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # inspired by "be my eyes"
    notification_round = models.IntegerField(default=0, help_text="Notifications round (0=none, 1-3=rounds)")
    notified_volunteers = models.ManyToManyField(
        User, 
        related_name='notified_activities', 
        blank=True,
        help_text="Volunteers who have been notified for this activity"
    )
    
    # recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=20, 
        blank=True,
        choices=(
            ('DAILY', 'Zilnic'),
            ('WEEKLY', 'Săptămânal'),
            ('MONTHLY', 'Lunar'),
        )
    )
    
    class Meta:
        ordering = ['deadline', '-priority']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.animal.name} ({self.get_status_display()})"
    
    def is_overdue(self):
        from django.utils import timezone
        return self.status in ['PD', 'AS', 'IP'] and self.deadline < timezone.now()