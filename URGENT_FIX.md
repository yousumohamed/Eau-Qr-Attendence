# CRITICAL FIXES NEEDED

## ⚠️ models.py is CORRUPTED!

The Session model fields are missing. Here's what needs to be fixed:

### Fix the Session model (lines 69-82 in models.py):

Replace the Session class with this:

```python
class Session(models.Model):
    """Attendance session with QR code"""
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='sessions')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    session_date = models.DateField(default=timezone.now)
    session_start_time = models.TimeField(default=timezone.now)
    session_end_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    is_active = models.BooleanField(default=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['qr_token']),
            models.Index(fields=['session_date']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            hours = getattr(settings, 'SESSION_EXPIRY_HOURS', 2)
            self.expires_at = timezone.now() + timedelta(hours=hours)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at or not self.is_active

    def close_session(self):
        self.is_active = False
        self.closed_at = timezone.now()
        self.save()

    def attendance_count(self):
        return self.attendance_records.count()

    def __str__(self):
        return f"{self.title} - {self.session_date} ({self.classroom})"
```

### After fixing, run:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## ✅ What's Already Fixed:

1. ✅ base.html - Logo and favicon support
2. ✅ admin.py - Photo uploads and previews
3. ✅ views.py - redirect import added

---

## 📝 TODO:

1. **Fix models.py** - Add the Session fields back
2. **Run migrations** - After fixing models.py
3. **Add your logo images** to `static/assets/`
   - favicon.png (32x32 px)
   - header.png (200x40 px)

---

**PRIORITY: Fix models.py first, then restart server!**
